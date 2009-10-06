# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

import sys
 
from constants_base import *
sys.path.insert(0,'config') 
from site_configuration import *
from constants_configdependent import *

def BuildURL(dir=None, page=None, query=None, extraSlash=False, rakontu=None):
	if dir:
		if DIRS.has_key(dir):
			dirString = DIRS[dir]
		else:
			dirString = dir # assume if it is not in the dictionary, they are specifying it directly
	else:
		dirString = None
	if page:
		if URLS.has_key(page):
			pageString = URLS[page]
		else:
			pageString = page # same here
	else: 
		pageString = None
	if dirString and pageString and query:
		result = "/%s/%s?%s" % (dirString, pageString, query)
	elif pageString and query:
		result = "/%s?%s" % (pageString, query)
	elif dirString and pageString:
		result = "/%s/%s" % (dirString, pageString)
	elif dirString:
		if extraSlash:
			result = "/%s/" % (dirString)
		else:
			result = "/%s" % (dirString)
	elif pageString:
		result = "/%s" % (pageString)
	else:
		result = "/"
	if rakontu:
		if query:
			result += "&"
		else:
			result += "?"
		result += rakontu.urlQuery()
	return result 
	
def BuildResultURL(query, rakontu=None):
	result = "/%s?%s=%s" % (URLS["url_result"], URL_OPTIONS["url_query_result"], RESULTS[query][0])
	if rakontu:
		result += "&" + rakontu.urlQuery()
	return result

def NotFoundURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_not_found"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_not_found"]
	
def AttachmentTooLargeURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_attachment_too_large"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_attachment_too_large"]
	
def AttachmentNotOfAcceptedFileTypeURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_attachment_wrong_type"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_attachment_wrong_type"]

def TransactionFailedURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_transaction_failed"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_transaction_failed"]
	
def DatabaseErrorURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_database_error"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_database_error"]
	
def NotAuthorizedURL(role, rakontu=None):
	if rakontu:
		return "/%s?%s&%s=%s" % (URLS["url_not_authorized"], rakontu.urlQuery(), URL_OPTIONS["url_query_role"], role)
	else:
		return "/%s?%s=%s" % (URLS["url_not_authorized"], URL_OPTIONS["url_query_role"], role)
	
def NoRakontuAndMemberURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_no_rakontu_and_member"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_no_rakontu_and_member"]
	
def ManagersOnlyURL(rakontu=None):
	if rakontu:
		return "/%s?%s" % (URLS["url_managers_only"], rakontu.urlQuery())
	else:
		return "/%s" % URLS["url_managers_only"]
	
def OwnersOnlyURL(rakontu):
	return "/%s?%s" % (URLS["url_owners_only"], rakontu.urlQuery())

def AdminOnlyURL():
	return "/%s" % URLS["url_admin_only"]
	
def DisplayTypeForEntryType(type):
	i = 0 
	for aType in ENTRY_TYPES:
		if aType == type:
			return ENTRY_TYPES_DISPLAY[i]
		i += 1
	raise "No translation for %s" % type

def URLForEntryType(type):
	i = 0
	for aType in ENTRY_TYPES:
		if aType == type:
			return ENTRY_TYPES_URLS[i]
		i += 1
	raise "No translation for %s" % type

def URLForAnnotationType(type):
	i = 0
	for aType in ANNOTATION_TYPES:
		if aType == type:
			return ANNOTATION_TYPES_URLS[i]
		i += 1
	raise "No translation for %s" % type

def DisplayTypeForLinkType(type):
	i = 0
	for aType in LINK_TYPES:
		if aType == type:
			return LINK_TYPES_DISPLAY[i]
		i += 1
	raise "No translation for %s" % type

def DisplayTypeForQuestionReferType(type):
	i = 0
	for aType in QUESTION_REFERS_TO:
		if aType == type:
			return QUESTION_REFERS_TO_DISPLAY[i]
		i += 1
	raise "No translation for %s" % type

def DisplayTypeForAnnotationType(type):
	i = 0
	for aType in ANNOTATION_TYPES:
		if aType == type:
			return ANNOTATION_TYPES_DISPLAY[i]
		i += 1
	raise "No translation for %s" % type

def URLForQuestionRefersTo(type):
	i = 0
	for aType in QUESTION_REFERS_TO:
		if aType == type:
			return QUESTION_REFERS_TO_URLS[i]
		i += 1
	raise "No translation for %s" % type

def DisplayTypePluralForQuestionRefersTo(type):
	i = 0
	for aType in QUESTION_REFERS_TO:
		if aType == type:
			return QUESTION_REFERS_TO_PLURAL_DISPLAY[i]
		i += 1
	raise "No translation for %s" % type

def stringUpTo(aString, aDelimiter):
    if len(aString) == 0:
        return ""
    delimiterPos = aString.find(aDelimiter)
    if delimiterPos == -1:
        result = aString
    elif delimiterPos == 0:
        result = ""
    else:
        result = aString[:delimiterPos]
    return result

def stringBeyond(aString, aDelimiter):
    if len(aString) == 0:
        result = ""
        return result
    delimiterPos = aString.find(aDelimiter)
    if delimiterPos == -1:
        result = aString
    elif delimiterPos == len(aString) - 1:
        result = ""
    else:
        result = aString[delimiterPos + 1:]
    return result

def stringBetween(startString, endString, wholeString):
    result = stringUpTo(stringBeyond(wholeString.strip(), startString), endString)
    return result
