import requests, json, os
from configparser import ConfigParser
from rich import print
from rich.prompt import Prompt
from rich.console import Console
from time import sleep

console = Console()

config = ConfigParser()
config.read('migrate.config.ini')

os.makedirs('export', exist_ok=True)
os.makedirs('export/items', exist_ok=True)

export_baseurl = config.get("EXPORT", "baseurl", fallback="")
restore_baseurl = config.get("IMPORT", "baseurl", fallback="")
export_access_token = config.get("EXPORT", "access_token", fallback="")
restore_access_token = config.get("IMPORT", "access_token", fallback="")

def export_data(name):
    
    result = requests.get(f"{export_baseurl}/{name}?access_token={export_access_token}")

    output = result.json()
    # print(output)
    if 'data' in output: output = output['data']
    
    if len(output) > 0 :
        
        if isinstance(output, list):
            
            data = []
            
            for p in output:
            
                if name == 'presets':
                    if not p['bookmark']: continue
                if name == "roles" and p['name'] == "Administrator": continue
                    
                data.append(p)
        
        elif isinstance(output, dict):
                
                data = output
                
        if data:
            # SAVE DATA
            with open(f'export/{name}.json', 'w') as outfile:
                json.dump({"data": data}, outfile)

def import_data(name, repeat_until_complete=False):
    
    existing_rows = []
    _data = {}
    # if name in ['presets']:
    #     result = requests.get(f"{restore_baseurl}/{name}?access_token={restore_access_token}&fields=bookmark,collection")
    #     if 'data' in result.json():
    #         # modified ID field to avoid the usage of ID which may be different
    #         _data = {"data": [{ "id": str(r['bookmark'])+str(r['collection']) } for r in result.json()['data']]}
    #         print(_data)
    # else:
    result = requests.get(f"{restore_baseurl}/{name}?access_token={restore_access_token}&fields=id")
    if 'data' in result.json():
        _data = result.json()
    if _data:
        # print(result.json())
        if len(_data['data']) > 0:
            if isinstance(_data['data'], list):
                existing_rows = [r['id'] for r in _data['data']]
            elif isinstance(_data['data'], dict) and 'id' in _data['data']:
                existing_rows = [_data['data']['id']]
    
    if os.path.exists(f'export/{name}.json'):
        with open(f'export/{name}.json') as json_file:
            rows = json.load(json_file)
            
        if rows:
            
            if name == 'settings': rows['data'] = [rows['data']]
            
            count = len(rows['data'])
            # print("rows['data']", count)
            
            while True:
                
                if count == 0: break
                                
                for row in rows['data']:

                    if row['id'] in existing_rows: 
                        count -= 1
                        print(f"[yellow]Already exists {name} {row['id']}.")
                        if not update: continue
                
                    # Create rows
                    
                    # drop params
                    if name == 'roles':
                        if 'users' in row: del row['users']
                    if name == 'presets':
                        # if 'id' in row: del row['id']
                        pass
                    if name == 'flows':
                        if 'user_created' in row: del row['user_created']
                        if 'operations' in row: del row['operations']    
                    if name == 'operations':
                        if 'user_created' in row: del row['user_created']
                        if 'date_created' in row: del row['date_created']
                    if name == 'settings':
                        if 'project_url' in row: del row['project_url']
                        if 'project_logo' in row: del row['project_logo'] # Uses foreign key for files. Assuming using different filesystem in devlopment.
                        if 'public_foreground' in row: del row['public_foreground'] # Uses foreign key for files. Assuming using different filesystem in devlopment.
                        if 'public_background' in row: del row['public_background'] # Uses foreign key for files. Assuming using different filesystem in devlopment.
                       
                    if update: 
                        if name == 'settings':
                            result = requests.patch(f"{restore_baseurl}/{name}?access_token={restore_access_token}", json=row)
                        else:
                            result = requests.patch(f"{restore_baseurl}/{name}/{row['id']}?access_token={restore_access_token}", json=row)
                    else: result = requests.post(f"{restore_baseurl}/{name}?access_token={restore_access_token}", json=row)
                    
                    # print(result.status_code)
                    # print(result.text)

                    if result.status_code == 200:
                        # print(result.json())  
                        _action = "Created" if not update else "Updated"
                        print(f"[green]{_action} {name} {row['id']}.")
                        existing_rows.append(row['id'])
                    else:
                        print(result.status_code)
                        print(result.text)
                    
                
                if not repeat_until_complete: break
                

def export_items(collection):
    
    result = requests.get(f"{export_baseurl}/items/{collection}?access_token={export_access_token}")

    output = result.json()
    # print(output)
    if 'data' in output: output = output['data']
    
    if len(output) > 0 :
        
        if isinstance(output, list):
            
            data = []
            
            for p in output:
                    
                data.append(p)
        
        elif isinstance(output, dict):
                
                data = output
                
        if data:
            # SAVE DATA
            with open(f'export/items/{collection}.json', 'w') as outfile:
                json.dump({"data": data}, outfile)
    
def import_items(collection, repeat_until_complete=False):
    
    existing_rows = []
    
    result = requests.get(f"{restore_baseurl}/items/{collection}?access_token={restore_access_token}&fields=id")
    if 'data' in result.json():
        # print(result.json())
        if len(result.json()['data']) > 0:
            if isinstance(result.json()['data'], list):
                existing_rows = [r['id'] for r in result.json()['data'] if 'id' in r]
            elif isinstance(result.json()['data'], dict) and 'id' in result.json()['data']:
                existing_rows = [result.json()['data']['id']]
    
    if os.path.exists(f'export/items/{collection}.json'):
        with open(f'export/items/{collection}.json') as json_file:
            rows = json.load(json_file)
            
        if rows:
                        
            count = len(rows['data'])
            # print("rows['data']", count)
            
            while True:
                
                for row in rows['data']:
                    
                    row_id = row['id'] if 'id' in row else None
                    
                    if row_id and row_id in existing_rows: 
                        count -= 1
                        print(f"[yellow]Already exists {collection} {row_id}.")
                        if not update: continue
                
                    # Create rows
                    
                    # drop params
                    for key in row.keys():
                        if any( k in key for k in ['user'] ):
                            del row[key]
                       
                    if update and row_id: 
                        result = requests.patch(f"{restore_baseurl}/items/{collection}/{row_id}?access_token={restore_access_token}", json=row)
                    else: result = requests.post(f"{restore_baseurl}/items/{collection}?access_token={restore_access_token}", json=row)
                    
                    # print(result.status_code)
                    # print(result.text)

                    if result.status_code == 200:
                        # print(result.json())  
                        _action = "Created" if not update else "Updated"
                        print(f"[green]{_action} {collection} {row_id}.")
                        if row_id: existing_rows.append(row_id)
                    else:
                        print("Status code",result.status_code)
                        print("Response",result.text)
                    
                
                if not repeat_until_complete: break
                
                if count == 0: break
    
def get_snapshot():
    url = f"{export_baseurl}/schema/snapshot?access_token={export_access_token}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200 and 'data' in data:
        with open(f'export/schema.json', 'w') as outfile:
            json.dump(data['data'], outfile)
        return data['data']
    else:
        print(f"[red]Error: {response.text}")
    return False

def get_diff(snapshot, force = False):
    if force:
        url = f"{restore_baseurl}/schema/diff?access_token={restore_access_token}&force=1"
    else:
        url = f"{restore_baseurl}/schema/diff?access_token={restore_access_token}"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=snapshot, headers=headers)
    data = response.json()
    if response.status_code == 200 and 'data' in data:
        with open(f'export/schema_diff.json', 'w') as outfile:
            json.dump(data['data'], outfile)
        return data['data']
    else:
        print(f"[red]Error: {response.text}")
    return False

def apply_diff(diff):
    url = f"{restore_baseurl}/schema/apply?access_token={restore_access_token}"
    headers = {'Content-Type': 'application/json'}
    response=requests.post(url, json=diff, headers=headers)
    if response.status_code == 200:
        return True
    else:
        print(f"[red]Error: {response.text}")
    return False
    
if __name__ == "__main__":
    
    _export = False if not export_baseurl or not export_access_token else True
    _import = False if not restore_baseurl or not restore_access_token else True
    
    print()
    console.rule("[bold red]Directus Migration Tool")
    print("[chartreuse2]This tool is intended to help you migrate data from one Directus instance to another.\nMain components are: [magenta]Schema, Flows, Bookmarks, Roles, File Folders, Webhooks, Permissions, Settings, Language Items.\n")
    print("[bold red]Permissions: You must be an admin user in both locations to use this tool.")
    console.rule("")

    if not _export or not _import:
        print("[red]Incomplete export and import baseurls and access_tokens in migrate.config.ini")
    
    # Schema
    if Prompt.ask("[bold][chartreuse2]Do you want to export/import schema? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if not all([_export,_import]):
            print("[bold red]Schema Migration requires BOTH source and destination to be set in migrate.config.ini")
        else:
            print("\n[bold red]Schema Migration")
            print("Notes: This does not allow different Directus versions and database vendors by default. This is to avoid any unintentional diffs from being generated. You can opt in to bypass these checks by using `force`.")
            force = True if Prompt.ask("[bold][chartreuse2]Do you want to force schema migration? (y/n): ", choices=['y','n'], default='n').lower() == 'y' else False
            Prompt.ask("Press Enter to start...")
            
            with console.status("Working..."):
                sleep(1)
                _success = False
                print("Generating snapshot...")
                snapshot = get_snapshot()
                if snapshot != False: 
                    sleep(1)
                    print("Generating diff...")
                    diff = get_diff(snapshot, force=force)
                    if diff != False: 
                        sleep(1)
                        print("Applying diff...")
                        if apply_diff(diff):
                            _success = True
            if _success:
                print("[green bold]Schema migration Done.")
            else:        
                print("[red bold]Schema migration FAILED.")
        print()
    
    update = True if Prompt.ask("[bold][chartreuse2]Do you want to update existing data? (y/n): ", choices=['y','n'], default='n').lower() == 'y' else False
    all = True if Prompt.ask("[bold][chartreuse2]Do you want to export and import all data? (y/n): ", choices=['y','n'], default='n').lower() == 'y' else False
    print()
    
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import Flows? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting flows...")
                export_data('flows')
                export_data('operations')
        if _import:
            with console.status("Working..."):
                print("Importing flows...")
                import_data('flows')
                import_data('operations', repeat_until_complete=True)
        
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import Bookmarks? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Bookmarks...")
                export_data("presets")
        if _import:
            with console.status("Working..."):
                print("Importing Bookmarks...")
                import_data("presets")
    
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import Roles? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Roles...")
                export_data("roles")
        if _import:
            with console.status("Working..."):
                print("Importing Roles...")
                import_data("roles")
    
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import File Folders? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Folders...")
                export_data("folders")
        if _import:
            with console.status("Working..."):
                print("Importing Folders...")
                import_data("folders")
    
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import File Webhooks? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Webhooks...")
                export_data("webhooks")
        if _import:
            with console.status("Working..."):
                print("Importing Webhooks...")
                import_data("webhooks")
    
    ## TODO - Permissions Import destination rows do not have ID ?! Because of New version?
    # if Prompt.ask("Are you sure you want to export and import Permissions? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
    #     if _export:
    #         print("Exporting Permissions...")
    #         export_data("permissions")
    #     if _import:
    #         print("Importing Permissions...")
    #         # import_data("permissions")
    
    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import Settings? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Settings...")
                export_data("settings")
        if _import:
            with console.status("Working..."):
                print("Importing Settings...")
                import_data("settings")

    if all or Prompt.ask("[bold][chartreuse2]Are you sure you want to export and import Language Options? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        if _export:
            with console.status("Working..."):
                print("Exporting Languages...")
                export_items("languages")
        if _import:
            with console.status("Working..."):
                print("Importing Languages...")
                import_items("languages")
    
    print()
    
    if Prompt.ask("[bold][chartreuse2]Do you want to export/import specific collection items? (y/n): ", choices=['y','n'], default='n').lower() == 'y':
        print("Please note, this may not work so well, especially if the data models are complicated or have relationships.")
        collections = input("Enter collection names separated by comma: ").lower().split(',')
        collections = [c.strip() for c in collections]
        
        for c in collections:
            if _export:
                with console.status("Working..."):
                    print(f"Exporting {c}...")
                    export_items(c)
            if _import:
                with console.status("Working..."):
                    print(f"Importing {c}...")
                    import_items(c)
        
    print()
    print("[green][bold]Done.")
    print()
    