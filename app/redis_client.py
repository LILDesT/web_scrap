import json
import redis
from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)


def save_task(task_id: str, task_data: dict):
    pipeline = redis_client.pipeline()
    pipeline.hset(f"task:{task_id}", mapping=task_data)
    pipeline.lpush(f"task_queue", task_id)
    pipeline.ltrim(f"task_queue", 0,  99)
    pipeline.expire(f"task:{task_id}", 86400)
    pipeline.execute()

def get_task_result(task_id: str) -> dict:
    data = redis_client.hgetall(f"task:{task_id}")
    if not data:
        return {}
    
    decoded_data = {}
    for key, value in data.items():
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
        decoded_data[key_str] = value_str
    
    if 'data' in decoded_data:
        if decoded_data['data']:
            try:
                decoded_data['data'] = json.loads(decoded_data['data'])
            except json.JSONDecodeError:
                decoded_data['data'] = {}
        else:
            decoded_data['data'] = {}
    
    return decoded_data

def update_task_status(task_id: str, status: str, data: dict = None, error: str = None):
    current_data = get_task_result(task_id)
    current_data.update({
        "status": status,
        "data": json.dumps(data) if data else "",
        "error": error or ""
    })
    save_task(task_id, current_data)

   