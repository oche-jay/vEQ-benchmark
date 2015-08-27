import logging
import numpy
from scipy import stats
import sys
import re
import logging

def validURLMatch(string_url):
    #See: http://daringfireball.net/2010/07/improved_regex_for_matching_urls
    '''
    Simple util to check if a string is a valid url
    '''
    GRUBER_URLINTEXT_PAT = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
    result =  GRUBER_URLINTEXT_PAT.search(string_url)
    return result

def validYoutubeURLMatch(string_url):
    '''
    Simple regex util to match youtube vids
    '''
    youtube_url_pattern = re.compile(ur'((http://)?)(www\.)?((youtube\.com/)|(youtu.be)|(youtube)).+')
    result = youtube_url_pattern.search(string_url)
    logging.debug("Youtube URL found")
    return result

def cleanResults(a_list,threshold=None):
    '''
    Take a list probabbly the results of a sqllite query
    Flatten it and then remove any values lower than zero
    Maybe
    '''
    a_list = list(sum(a_list,())) #flatten list
    a_list[:] = [x for x in a_list if x > 0] #retain values if > 0
    return a_list

def outliers(a):
    """Input is array of numbers. Output is tuple: lower outer fence,
    lower inner fence, median, upper inner fence, upper outer fence.
    """
    s = sorted(a)
    Q2 = numpy.median(s)
    midpoint = len(s) / 2
    Q1 = numpy.median(s[:midpoint])
    Q3 = numpy.median(s[midpoint:])
    interq_range = Q3 - Q1
    innerQ1 = Q1 - interq_range * 1.5
    innerQ3 = Q3 + interq_range * 1.5
    outerQ1 = Q1 - interq_range * 3.
    outerQ3 = Q3 + interq_range * 3.
    assert outerQ1 <= innerQ1 <= Q2 <= innerQ3 <= outerQ3

    return outerQ1,innerQ1,Q2,innerQ3,outerQ3

def getConfidence(power_np):
    confidence_level=0.95
    confidence_interval = stats.sem(power_np) * stats.t._ppf((1+confidence_level)/2, len(power_np)-1)
    return confidence_interval
    
    
def getMean(numpy_array):
    def reject_outliers(data, m=2):
        """
        http://stackoverflow.com/questions/11686720/is-there-a-numpy-builtin-to-reject-outliers-from-a-list
        """
        
        outliers = data[abs(data - numpy.mean(data)) > m * numpy.std(data)]
        logging.warn("Outliers detected  - rejecting the following values" + str(outliers))
#         print "Outliers detected - rejecting the following values" + str(outliers)
        return data[abs(data - numpy.mean(data)) < m * numpy.std(data)]
        
    try:
        return numpy.mean(reject_outliers(numpy_array, 3))
    except:
        logging.error(sys.exc_info()[1])
        return "N/A"