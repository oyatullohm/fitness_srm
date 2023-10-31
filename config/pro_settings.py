from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ['*']

import dj_database_url
DATABASES = {
    'default': dj_database_url.parse('postgres://oyatilla:MZpaOJbZGTPjlAmA57jPifVnZ2n4eSnN@dpg-cl0c79i37rbc739666qg-a.oregon-postgres.render.com/oyatilla')


__all__ = ['ALLOWED_HOSTS',"DATABASES"]
