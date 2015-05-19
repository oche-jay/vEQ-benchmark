
def cleanResults(a_list,threshold=None):
    '''
    Take a list probabbly the results of a sqllite query
    Flatten it and then remove any values lower than zero
    Maybe
    '''
    a_list = list(sum(a_list,())) #flatten list
    a_list[:] = [x for x in a_list if x > 0] #retain values if > 0
    return a_list