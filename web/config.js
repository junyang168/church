var env = 'dev'
api_prefix = env == 'dev'? 'http://localhost:8000/api/' :'/api/'    
saveDelay = env == 'dev'? 3000 : 10000

