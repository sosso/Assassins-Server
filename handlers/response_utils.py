def get_response_dict(success_bool, error_reason=None):
    response_dict = {}
    if success_bool:
        response_dict['success'] = "success"
    else:
        response_dict['success'] = "error"
        response_dict['reason'] = error_reason
    return response_dict
        
        