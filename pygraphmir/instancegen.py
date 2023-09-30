
next_instance_id = 0
def get_next_instance_id():
    global next_instance_id
    ret_id = next_instance_id
    next_instance_id += 1
    return ret_id
