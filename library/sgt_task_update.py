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

ALLOW_CLOSE_CODES = ("Successful", "Successful automatic", "Successful with issues", "Unsuccessful", "Cancelled", "Rejected")

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

    return response

def update_task(task_number, task_id, data, **module_args):
    response = None
    endpoint = module_args["sn_base"] + module_args["sn_uri"] + "/" + task_id

    if "work_notes" in module_args:
        data.update({ "work_notes": module_args["work_notes"] })

    try:
        response = requests.put(
            url=endpoint,
            auth=(module_args["sn_user"], module_args["sn_pass"]),
            data=json.dumps(data),
            timeout=module_args["timeout"]
        )

    except Exception as e:
        response = {"mensaje": "ERROR, task could not updated: "+str(task_number)+": " + str(e)}
        
    return response


def validateOptions(module):
    
    if module.params["state"] == "in_progress":

        module.params["status"] = "Work in Progress"
        response = info(module.params["task"], **module.params).json()
        task_id = ""
        data={
            "state": module.params["status"],
            "assigned_to": module.params["assigned_to"]
        }
        
        if len(response["result"]) > 0:
            task_id = response["result"][0]["sys_id"]
            
        
        return update_task(module.params["task"], task_id, data, **module.params)
    
    else:
    
        if module.params["state"] == "closed":
            module.params["status"] = "Closed Complete"
        
        if module.params["state"] == "incomplete":
            module.params["status"] = "Closed Incomplete"
        
        if module.params["state"] == "skipped":
            module.params["status"] = "skipped"
        
        if module.params["close_code"] not in ALLOW_CLOSE_CODES:
            return {"result": {"mensaje":"close_code does not meet with catalog codes" } }
        
        response = info(module.params["task"], **module.params).json()
        task_id = ""
        data={
            "state": module.params["status"],
            "u_close_code": module.params["close_code"],
            "close_notes": module.params["close_notes"]
        }

        
        if len(response["result"]) > 0:
            task_id = response["result"][0]["sys_id"]
            
        
        return update_task(module.params["task"], task_id, data, **module.params)
    
    

def run_module():
    
    module_args = {
        "state": {
            "default": "in_progress",
            "choices": ["in_progress", "closed","incomplete","skipped"]
        },
        "sn_user": {"required": False, "type": "str"},
        "sn_pass": {"required": False, "type": "str", "no_log": True},
        "sn_base": {"required": True, "type": "str"},
        "sn_uri": {"required": False, "type": "str", "default": "/api/now/v2/table/rm_task"},
        "timeout": {"required": False, "type": "int", "default": 300},

        #For updating
        "task":{ "type": "str" },

        #For updating
        "assigned_to":{"type":"str"},
        "work_notes":{"type":"str"},
        "close_code":{"type":"str"},
        "close_notes":{"type":"str"},
        
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
            ('state', 'in_progress', ('task', 'assigned_to' ), False),
            ('state', 'closed', ('task', 'close_code', 'close_notes' ), False)
            ('state', 'incomplete', ('task', 'close_code', 'close_notes' ), False)
            ('state', 'skipped', ('task', 'close_code', 'close_notes' ), False)
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
        module.fail_json(msg="Response generic error: ",**result)

def main():
    run_module()

if __name__ == '__main__':
    main()