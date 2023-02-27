#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
import requests
import json
from datetime import datetime


###DOCUMENTATION = r'''
###---
###module: onefcc_snow_task
###
###short_description: Modulo de Tasks para ONEFCC Service Now
###
###version_added: "1.0.0"
###
###description: Modulo para crear, cerrar y obtener informacion acerca de las tasks.
###
###options:
###    state:
###        description: Es para indicar la opcion a realizar dentro de la task
###            - info_task. Para obtener informacion a cerca de la task
###            - incomplete.
###        required: false
###        type: bool
###    task:
###        description: Numero de la tarea a buscar, requerido si info_task esta presente
###        required: true
###        type: str
###    
###
#### Specify this value according to your collection
#### in format of namespace.collection.doc_fragment_name
###extends_documentation_fragment:
###    - my_namespace.my_collection.my_doc_fragment_name
###
###author:
###    - Marco Rea (@x25241)
###'''
###
###EXAMPLES = r'''
#### Pass in a message
###- name: Test with a message
###  my_namespace.my_collection.my_test:
###    name: hello world
###
#### pass in a message and have changed true
###- name: Test with a message and changed output
###  my_namespace.my_collection.my_test:
###    name: hello world
###    new: true
###
#### fail the module
###- name: Test failure of the module
###  my_namespace.my_collection.my_test:
###    name: fail me
###'''
###
###RETURN = r'''
#### These are examples of possible return values, and in general should use other names for return values.
###original_message:
###    description: The original name param that was passed in.
###    type: str
###    returned: always
###    sample: 'hello world'
###message:
###    description: The output message that the test module generates.
###    type: str
###    returned: always
###    sample: 'goodbye'
###'''

TASK_STATE_CODES = { "open": 1, "pending": 5, "in_progress": 2, "closed": 3, "incomplete": 4,  "skipped": 7, "all":""  }
TASK_STATE_RESOLVE_CODES = { "pre-production":15, "implement":9, "all":"" }

def info(task_number, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] 
    params={"sysparm_query": "number="+str(task_number) }

    try:
        response = requests.get(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            params=params,
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, task could not get information: "+str(task_number)+": " + str(e)}
        #log("ERROR, no se pudo crear la release: " + str(e))

    return response

def info_all_tasks(release_number, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] 
    q="top_task.number="+str(release_number)+"^state=^u_state_to_resolve="

    if module_args["state_resolve"] == "all":
        q = q.replace("^u_state_to_resolve=", TASK_STATE_RESOLVE_CODES[ module_args["state_resolve"] ])
    else:     
        q = q.replace("^u_state_to_resolve=", "^u_state_to_resolve="+str( TASK_STATE_RESOLVE_CODES[ module_args["state_resolve"] ] ))
    
    if module_args["info_tasks_filter"] == "all":       
        q = q.replace("^state=", TASK_STATE_CODES[ module_args["info_tasks_filter"] ])
    else:
        q = q.replace("^state=", "^state="+str( TASK_STATE_CODES[ module_args["info_tasks_filter"] ] ))

    params={
        "sysparm_display_value": "true",
        "sysparm_query": q,
        "sysparm_fields": "number,u_state_to_resolve,state,sys_id"
    }

    try:
        response = requests.get(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            params=params,
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, no se pudo obtener información de las tasks asociadas a "+str(release_number)+": " + str(e)}

    return response

def validateOptions(module):
    
    if module.params["state"] == "info":
        return info(module.params["task"], **module.params)

    if module.params["state"] == "info_tasks":
        return info_all_tasks(module.params["release"], **module.params)



def run_module():
    
    module_args = {
        "state": {
            "default": "present",
            "choices": ["info", "info_tasks"]
        },
        "sn_user": {"required": False, "type": "str"},
        "sn_pass": {"required": False, "type": "str", "no_log": True},
        "sn_base": {"required": True, "type": "str"},
        "sn_uri": {"required": False, "type": "str", "default": "/api/now/v2/table/rm_task"},
        "timeout": {"required": False, "type": "int", "default": 300},

        #Para info, work in progress, complete task
        "task": {"type": "str"},

        #Para info tasks
        "release":{ "type": "str" }, 
        "info_tasks": {"type":"str"},
        "info_tasks_filter": {"type":"str", "default":"open"}

    }

    result = dict(
        changed=False,
        original_message="",
        message=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[
            ('state', 'info', ('task', 'sn_user', 'sn_pass','sn_base') ),
            ('state', 'info', ('task', 'sn_user', 'sn_pass','sn_base') )
        ]   
    )

    if module.check_mode:
        module.exit_json(**result)
    else:
        response = validateOptions(module)

    result["message"] = json.loads(response.text)
    #result["message"] = json.loads(response.json())

    if response.status_code == 200 or response.status_code == 201:
        
        #Sólo consulta
        if module.params["state"] == "info" or module.params["state"] == "info_tasks":
            if len(response.json()['result']) > 0:
                result['message'] = response.json()["result"]
                result['changed'] = True
            else:
                result['message'] = "No records found!"
                result['changed'] = False
        #Aplica para otras acciones
        else:

            resp = response.json()

            if "number" in resp["result"] or "sys_id" in resp["result"]:
                result['message'] = resp["result"]
                result['changed'] = True
            else:
                result['message'] = "Action could not be executed: "+module.params["state"]
                result['changed'] = False
                module.fail_json(msg="Response generic error: "+str(response), **result)
            
        module.exit_json(**result)

    else:
        module.fail_json(msg="Response generic error",**result)

def main():
    run_module()

if __name__ == '__main__':
    main()