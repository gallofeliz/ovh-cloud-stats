#!/usr/bin/env python
import ovh
import http.server, json, logging, os, socketserver

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
port = int(os.environ.get('PORT', 80))
# https://api.ovh.com/createToken
client = ovh.Client(
    endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
    application_key=os.environ['OVH_APPLICATION_KEY'],
    application_secret=os.environ['OVH_APPLICATION_SECRET'],
    consumer_key=os.environ['OVH_CONSUMER_KEY']
)

def get_stats():

    stats = []
    projects = client.get('/cloud/project')

    for project_id in projects:
        project = client.get('/cloud/project/' + project_id)
        containers = client.get('/cloud/project/' + project_id + '/storage')

        for _container in containers:
            container = client.get('/cloud/project/' + project_id + '/storage/' + _container['id'], noObjects=True)

            stats.append({
                "stat": "object-storage",
                "project": {
                    "id": project['project_id'],
                    "name": project['description']
                },
                "region": container['region'],
                "container": {
                    "id": _container['id'],
                    "name": container['name'],
                },
                'storedObjects': container['storedObjects'],
                'storedBytes': container['storedBytes']
            })

        usage = client.get('/cloud/project/' + project_id + '/usage/current')

        for storage_usage in usage['hourlyUsage']['storage']:
            stats.append({
                "stat": "hourly-storage-usage",
                "project": {
                    "id": project['project_id'],
                    "name": project['description']
                },
                "region": storage_usage['region'],
                'totalPrice': storage_usage['totalPrice'],
                'outgoingBandwidth': {
                    'quantityBytes': round(storage_usage['outgoingBandwidth']['quantity']['value'] * 1024 * 1024 * 1024) if storage_usage['outgoingBandwidth'] else 0,
                    'totalPrice': storage_usage['outgoingBandwidth']['totalPrice'] if storage_usage['outgoingBandwidth'] else 0
                },
                'stored': {
                    'quantityBytesHour': round(storage_usage['stored']['quantity']['value'] * 1024 * 1024 * 1024) if storage_usage['stored'] else 0,
                    'totalPrice': storage_usage['stored']['totalPrice'] if storage_usage['stored'] else 0
                }
            })

    return stats

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if (self.path == '/favicon.ico'):
            return

        try:
            data = get_stats()

            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(data), 'utf8'))
        except Exception as inst:
             self.send_response(500)
             self.send_header('Content-type','text/html')
             self.end_headers()
             self.wfile.write(bytes(str(inst), 'utf8'))
             logging.exception('Error')

httpd = socketserver.TCPServer(('', port), Handler)
try:
   httpd.serve_forever()
except KeyboardInterrupt:
   pass
httpd.server_close()
