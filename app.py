#!/usr/bin/env python
import ovh
import http.server, json, logging, os, socketserver

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
port = int(os.environ.get('PORT', 8080))
# https://api.ovh.com/createToken
client = ovh.Client(
    endpoint='ovh-eu',               # Endpoint of API OVH Europe (List of available endpoints)
    application_key=os.environ['OVH_APPLICATION_KEY'],
    application_secret=os.environ['OVH_APPLICATION_SECRET'],
    consumer_key=os.environ['OVH_CONSUMER_KEY']
)

def get_stats():
    projects = client.get('/cloud/project')

    data = {
        'totalContainers': 0,
        'totalObjects': 0,
        'totalBytes': 0,
        'totalMonthlyPrice': 0,
        'totalStorageMonthlyPrice': 0,
        'totalBandwidthMonthyPrice': 0,
        'projects': []
    }

    for project_id in projects:
        project = client.get('/cloud/project/' + project_id)
        project_data = {
            'name': project['description'], # key is description but is name in UI
            'totalContainers': 0,
            'totalObjects': 0,
            'totalBytes': 0,
            'totalMonthlyPrice': 0,
            'totalStorageMonthlyPrice': 0,
            'totalBandwidthMonthyPrice': 0,
            'containers': []
        }
        data['projects'].append(project_data)
        storages = client.get('/cloud/project/' + project_id + '/storage')
        print(storages)
        for storage in storages:
            real_storage = client.get('/cloud/project/' + project_id + '/storage/' + storage['id'], noObjects=True)
            project_data['totalContainers'] += 1
            project_data['totalBytes'] += real_storage['storedBytes']
            project_data['totalObjects'] += real_storage['storedObjects']
            container = {
                'name': storage['name'],
                'totalBytes': real_storage['storedBytes'],
                'totalObjects': real_storage['storedObjects']
            }
            project_data['containers'].append(container)

        usage = client.get('/cloud/project/' + project_id + '/usage/current')
        storage_usage = usage['hourlyUsage']['storage']

        for usage in storage_usage:
            project_data['totalMonthlyPrice'] += usage['totalPrice']
            project_data['totalStorageMonthlyPrice'] += usage['stored']['totalPrice'] if usage['stored'] else 0
            project_data['totalBandwidthMonthyPrice'] += usage['outgoingBandwidth']['totalPrice']

        data['totalContainers'] += project_data['totalContainers']
        data['totalBytes'] += project_data['totalBytes']
        data['totalObjects'] += project_data['totalObjects']
        data['totalMonthlyPrice'] += project_data['totalMonthlyPrice']
        data['totalStorageMonthlyPrice'] += project_data['totalStorageMonthlyPrice']
        data['totalBandwidthMonthyPrice'] += project_data['totalBandwidthMonthyPrice']

        return data

class Handler(http.server.SimpleHTTPRequestHandler):
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
