import requests
import ndjson
import sys, getopt
import json

# def export_dashboards(kibana_server, user, password, admin_space_id, object_ids):
#     data = {
#         "objects": [],
#         "includeReferencesDeep": True
#     }
#     for object in object_ids:
#         data['objects'].append(object)

#     if admin_space_id == 'default':
#         URL = f"{kibana_server}/api/saved_objects/_export"
#     else:
#         URL = f"{kibana_server}/s/{admin_space_id}/api/saved_objects/_export"

#     #print(URL)
#     resp = requests.post(URL, json=data, auth=(user, password), headers={"kbn-xsrf": "reporting"})
#     #print(resp.content)
#     return resp.content

# def retry_dashboards(kibana_server, user, password, viewer_space_id, integration_dashboards, errors, successResults):
#     retries = []
#     for error in errors:
#         retry = {'id': error['id'], 'type': error['type'], 'overwrite': True, 'ignoreMissingReferences': True}
#         retries.append(retry)

#     # for success in successResults: 
#     #     retry = {'id': error['id'], 'type': error['type'], 'overwrite': True}
#     #     retries.append(retry)

#     if viewer_space_id == 'default':
#         URL = f"{kibana_server}/api/saved_objects/_resolve_import_errors"
#     else:
#         URL = f"{kibana_server}/s/{viewer_space_id}/api/saved_objects/_resolve_import_errors"
#     print(retries)
#     resp = requests.post(URL, files={"file": ("export.ndjson", integration_dashboards), "retries": (None, json.dumps(retries))}, auth=(user, password), headers={"kbn-xsrf": "reporting"}, params={'compatibilityMode': True, 'createNewCopies': False})   
#     print(resp)

# def import_dashboards(kibana_server, user, password, viewer_spaces, integration_dashboards):
#     for space in viewer_spaces:
#         if space == 'default':
#             URL = f"{kibana_server}/api/saved_objects/_import"
#         else:
#             URL = f"{kibana_server}/s/{space}/api/saved_objects/_import"
#         #print(URL)
#         resp = requests.post(URL, files={"file": ("export.ndjson", integration_dashboards)}, auth=(user, password), headers={"kbn-xsrf": "reporting"}, params={'compatibilityMode': True, 'overwrite': True})   
#         #print(resp.content)
#         print(f"importing dashboards into space:{space}...")
#         if resp.json()['success'] == False:
#             print(f"error importing some objects")
#             retry_dashboards(kibana_server, user, password, space, integration_dashboards, resp.json()['errors'],resp.json()['successResults'])

def get_integration_dashboards(kibana_server, user, password, admin_space_id):
    data = {
        "type": "dashboard",
        "includeReferencesDeep": True
    }
    URL = f"{kibana_server}/s/{admin_space_id}/api/saved_objects/_export"
    #print(URL)
    resp = requests.post(URL, json=data, auth=(user, password), headers={"kbn-xsrf": "reporting"})
    objects = ndjson.loads(resp.content)
    integration_object_ids = []
    for obj in objects:
        if 'references' in obj:
            for ref in obj['references']:
                if ref['type'] == 'tag':
                    if ref['id'].find('fleet') != -1:
                        if not obj['id'] in integration_object_ids and 'type' in obj and obj['type'] == 'dashboard':
                            #print(obj)
                            if 'type' in obj:
                                integration_object_ids.append({'type': obj['type'], 'id': obj['id']})
                        break
    print(integration_object_ids)
    return integration_object_ids

def copy_dashboards(kibana_server, user, password, admin_space_id, object_ids, viewer_space_ids):
    data = {
        "objects": [],
        "includeReferences": True,
        "overwrite": True,
        "compatibilityMode": True,
        "createNewCopies": False,
        "spaces": viewer_space_ids
    }
    for object in object_ids:
        data['objects'].append(object)

    if admin_space_id == 'default':
        URL = f"{kibana_server}/api/spaces/_copy_saved_objects"
    else:
        URL = f"{kibana_server}/s/{admin_space_id}/api/spaces/_copy_saved_objects"
    resp = requests.post(URL, json=data, auth=(user, password), headers={"kbn-xsrf": "reporting"})
    print(resp.content)
    return resp.content


def get_viewer_space_ids(kibana_server, user, password, admin_space_id):
    URL = f"{kibana_server}/api/spaces/space"
    #print(URL)
    resp = requests.get(URL, auth=(user, password), headers={"kbn-xsrf": "reporting"})
    viewer_space_ids = []
    for space in resp.json():
        if space['id'] != admin_space_id:
            viewer_space_ids.append(space['id'])
    #print(viewer_space_ids)
    return viewer_space_ids

def replicate_integration_dashboards(kibana_server, user, password, admin_space_id, viewer_space_ids=None):

    integration_object_ids = get_integration_dashboards(kibana_server, user, password, admin_space_id)
    print(integration_object_ids)

    if viewer_space_ids == None:
        viewer_space_ids = get_viewer_space_ids(kibana_server, user, password, admin_space_id)

    copy_dashboards(kibana_server, user, password, admin_space_id, integration_object_ids, viewer_space_ids)
    #integration_dashboards = export_dashboards(kibana_server, user, password, admin_space_id, integration_object_ids)
    #import_dashboards(kibana_server, user, password, viewer_space_ids, integration_dashboards)

def main(argv):
    opts, args = getopt.getopt(argv,"s:u:p:a:")

    for opt, arg in opts:
        if opt in ("-s"):
            server = arg
        elif opt in ("-u"):
            user = arg
        elif opt in ("-p"):
            passw = arg
        elif opt in ("-a"):
            admin_space_id = arg

    replicate_integration_dashboards(server, user, passw, admin_space_id)

if __name__ == "__main__":
    main(sys.argv[1:])

#example, assuming you installed integrations into the "default" space
#python main.py -s "https://serverabc123.kb.us-central1.gcp.cloud.es.io:9243" -u "elastic" -p "XYZ123" -a "default"