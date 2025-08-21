#!/usr/bin/env python3
import requests
import json
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

API_BASE = "http://localhost:8000"

def test_api_health():
    """Бьется ли сердце у API?"""
    try:
        response = requests.get(f"{API_BASE}/docs")
        return {"status": "OK", "code": response.status_code}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def test_create_task(url):
    """Создает задачу"""
    try:
        response = requests.post(
            f"{API_BASE}/tasks",
            json={"url": url},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return {"status": "OK", "task_id": response.json()["task_id"]}
        else:
            return {"status": "FAILED", "code": response.status_code}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def test_task_status(task_id):
    """Получает статус задачи"""
    try:
        response = requests.get(f"{API_BASE}/tasks/{task_id}")
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "OK",
                "task_status": data.get("status"),
                "data_count": len(data.get("data", [])) if data.get("data") else 0,
                "error": data.get("error")
            }
        else:
            return {"status": "FAILED", "code": response.status_code}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def test_domain_limiter_stats():
    """Получает статистику ограничений доменов"""
    try:
        response = requests.get(f"{API_BASE}/stats/domain-limiter")
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "OK",
                "max_concurrent": data["config"]["max_concurrent_per_domain"],
                "domains": list(data["domain_stats"].keys()),
                "domain_count": len(data["domain_stats"])
            }
        else:
            return {"status": "FAILED", "code": response.status_code}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def test_concurrent_domain_limits():
    """Ограничения доменов (3 одновременных запроса)"""
    urls = [
        "https://24.kz/kz",
        "https://24.kz/ru", 
        "https://24.kz/en",
        "https://24.kz/kz?page=2",
        "https://24.kz/ru?page=2"
    ]
    
    results = []
    task_ids = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(test_create_task, url) for url in urls]
        for future in futures:
            result = future.result()
            results.append(result)
            if result["status"] == "OK":
                task_ids.append(result["task_id"])
    
    time.sleep(2)
    stats = test_domain_limiter_stats()
    
    return {
        "created_tasks": len([r for r in results if r["status"] == "OK"]),
        "failed_tasks": len([r for r in results if r["status"] == "FAILED"]),
        "task_ids": task_ids,
        "domain_stats": stats
    }

def test_scraping_workflow():
    """Полный рабочий процесс"""
    test_url = "https://24.kz/kz"
    
    create_result = test_create_task(test_url)
    if create_result["status"] != "OK":
        return {"status": "FAILED", "step": "create_task", "error": create_result}
    
    task_id = create_result["task_id"]
    
    for i in range(60):
        time.sleep(1)
        status_result = test_task_status(task_id)
        
        if status_result["status"] == "OK":
            task_status = status_result["task_status"]
            
            if task_status == "SUCCESS":
                return {
                    "status": "OK",
                    "task_id": task_id,
                    "execution_time": i + 1,
                    "news_count": status_result["data_count"],
                    "final_status": status_result
                }
            elif task_status == "FAILED":
                return {
                    "status": "FAILED", 
                    "step": "task_failed",
                    "error": status_result["error"]
                }
    
    return {"status": "TIMEOUT", "task_id": task_id, "waited": 60}

def run_all_tests():
    """Запуск всех тестов и сохранение в JSON"""
    print("🚀 Запуск тестирования веб-скрапера...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    print("📡 Тест API...")
    results["tests"]["api_health"] = test_api_health()
    
    print("📊 Тест статистики доменов...")
    results["tests"]["domain_stats_initial"] = test_domain_limiter_stats()
    
    print("🔒 Тест ограничений доменов...")
    results["tests"]["concurrent_limits"] = test_concurrent_domain_limits()
    
    print("⚙️ Тест рабочего процесса...")
    results["tests"]["scraping_workflow"] = test_scraping_workflow()
    
    print("📈 Финальная статистика...")
    time.sleep(2)
    results["tests"]["domain_stats_final"] = test_domain_limiter_stats()
    
    filename = f"test_results_{int(time.time())}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Тестирование завершено! Результаты сохранены в {filename}")
    
    print("\n📋 КРАТКИЙ ОТЧЕТ:")
    for test_name, test_result in results["tests"].items():
        status = "✅" if test_result.get("status") == "OK" else "❌"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    run_all_tests()
