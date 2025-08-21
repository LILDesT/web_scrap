import asyncio
import aiohttp
from bs4 import BeautifulSoup
from celery import current_task
from app.celery import celery
from app.config import settings
from app.reqest_utils import make_request
from app.redis_client import update_task_status

async def scrape_url_async(url, task_id):
    connector = aiohttp.TCPConnector(limit_per_host=settings.MAX_CONCURRENT_REQUESTS_PER_DOMAIN)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            update_task_status(task_id, 'PENDING', {})
            
            html = await make_request(url, session)
            
            if html:
                result = parse_html(html)
                
                update_task_status(task_id, 'SUCCESS', result)
                return result
            else:
                error_msg = "Failed to fetch HTML content"
                update_task_status(task_id, 'FAILED', {}, error=error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            update_task_status(task_id, 'FAILED', {}, error=str(e))
            raise e

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    news_items = []
    
    selectors = [
        'article',
        '.entry',
        '.entry_card',
        '.news-item',
        '.post',
        'div[class*="entry"]',
        'div[class*="article"]',
        'div[class*="news"]',
        'div[class*="card"]'
    ]
    
    articles = []
    for selector in selectors:
        found = soup.select(selector)
        if found:
            articles = found
            print(f"Found {len(found)} articles using selector: {selector}")
            break
    
    if not articles:
        containers = soup.find_all('div', class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['entry', 'article', 'news', 'post', 'card', 'item', 'block']
        ))
        articles = containers
        print(f"Found {len(articles)} containers by class keywords")
    
    for article in articles:
        try:
            # Ищем (entity_title)
            title = None
            title_selectors = [
                
                '.entry_title',
                'h2.entry_title', 
                'h3.entry_title',
                # Альтернативные варианты
                '.entity_title',
                '.entry-title',
                'h1', 'h2', 'h3', 'h4',
                '.title',
                '.headline',
                'a[href*="/news/"]',
                'a[href*="/world/"]',
                'a[href*="/"]',  # Любые ссылки
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                title_elem = article.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # Фильтруем заголовки и мусор
                    if title and len(title) > 10 and not title.isdigit():
                        break
            
            # Ищем дату (entry_meta_date)
            date = None
            date_selectors = [
                # Точные классы
                '.entry_meta_date',
                'li.entry_meta_date',
                # Альтернативные варианты
                '.entry-meta-date',
                '.entry_meta .entry_meta_date',
                '.meta_date',
                '.date',
                '.publish-date',
                '.entry-date',
                'time',
                '[datetime]',
                '[class*="date"]',
                '[class*="time"]',
                '.entry_meta li',  # Элементы внутри метаданных
                '.meta li'
            ]
            
            for selector in date_selectors:
                date_elem = article.select_one(selector)
                if date_elem:
                    date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    if date and len(date) < 50: 
                        break
            
            
            url = None
            # Ищем ссылку в заголовке или в статье
            link_selectors = [
                'a[href*="/news/"]',
                'a[href*="/world/"]', 
                '.entry_title a',
                'h2 a',
                'h3 a',
                'a[href]'
            ]
            
            for selector in link_selectors:
                link_elem = article.select_one(selector)
                if link_elem and link_elem.get('href'):
                    url = link_elem['href']
                    
                    if url.startswith('/'):
                        url = f"https://24.kz{url}"
                    elif url.startswith('http'):
                        pass 
                    else:
                        url = f"https://24.kz/{url}"
                    break
            
            
            if title and len(title) > 5:
                news_item = {
                    'entity_title': title,
                    'entry_meta_date': date or 'Дата не найдена',
                    'url': url or 'URL не найден'
                }
                news_items.append(news_item)
                
        except Exception as e:
           
            print(f"Error parsing article: {e}")
            continue
    
    
    if not news_items:
        print("No articles found, trying fallback method...")
        
        
        title_elements = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=True)
        for title_elem in title_elements[:15]: 
            title = title_elem.get_text(strip=True)
            if len(title) > 10 and not title.isdigit():
               
                date = 'Дата не найдена'
                parent = title_elem.parent
                if parent:
                    date_elem = parent.find(class_=lambda x: x and 'date' in x.lower())
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                
                
                url = 'URL не найден'
                link = title_elem.find('a') or (title_elem.parent and title_elem.parent.find('a'))
                if link and link.get('href'):
                    url = link['href']
                    if url.startswith('/'):
                        url = f"https://24.kz{url}"
                
                news_items.append({
                    'entity_title': title,
                    'entry_meta_date': date,
                    'url': url
                })
    
    print(f"Total news items found: {len(news_items)}")
    return news_items

@celery.task(bind=True, name='app.tasks.scrape_url', max_retries=settings.MAX_RETRIES)
def scrape_url(self, url):
    task_id = self.request.id
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(scrape_url_async(url, task_id))
        return result
    except Exception as exc:
        if "Access forbidden (403)" in str(exc):
            update_task_status(task_id, 'FAILED', {}, error="Access forbidden (403) - no retries")
            raise exc
        
        retry_count = self.request.retries
        if retry_count < settings.MAX_RETRIES:
            countdown = (settings.RETRY_BACKOFF ** retry_count) * 2
            print(f"Celery retry {retry_count + 1}/{settings.MAX_RETRIES} after {countdown}s")
            raise self.retry(exc=exc, countdown=countdown, max_retries=settings.MAX_RETRIES)
        else:
            update_task_status(task_id, 'FAILED', {}, error=f"Max retries exceeded: {str(exc)}")
            raise exc
