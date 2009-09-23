﻿# ============================================================================================
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# ============================================================================================

import logging, pytz, re, csv, uuid, random
from datetime import *
from pytz import timezone
from google.appengine.api import memcache

VERSION_NUMBER = "0.9"

from translationLookup import *

from google.appengine.ext import db
import pager

def GenerateSequentialKeyName(type):
	IncrementCount(type)
	return "%s%s" % (type, GetShardCount(type))

def GetShardCount(type):
	result = 0
	for counter in CounterShard.all().filter("type = ", type).fetch(FETCH_NUMBER):
		result += counter.count
	return result

def IncrementCount(type):
	config = CounterShardConfiguration.get_or_insert(type, type=type)
	def transaction():
		i = random.randint(0, config.numShards - 1)
		shardKeyName = type + str(i)
		counter = CounterShard.get_by_key_name(shardKeyName)
		if not counter:
			counter = CounterShard(key_name=shardKeyName, type=type)
		counter.count += 1
		counter.put()
	db.run_in_transaction(transaction)
	
def IncreaseNumberOfShards(type, number):
	config = CounterShardConfiguration.get_or_insert(type, type=type)
	def transaction():
		if config.numShards < number:
			config.numShards = number
			config.put()
	db.run_in_transaction(transaction)
	
def DebugPrint(text, msg="print"):
	logging.info(">>>>>>>> %s >>>>>>>> %s" %(msg, text))
	
def stripTags(text):
	if text:
		tags = re.compile(r'\<(.+?)\>').findall(text)
		for tag in tags:
			text = text.replace('<%s>' % tag, " ")
		text = text.replace("  ", " ")
		return text
	else:
		return "none"
   
def CleanUpCSV(parts):
	partsWithCommasQuoted = []
	for part in parts:
		if part:
			cleanPart = part
			cleanPart = cleanPart.replace('"', '""')
			if cleanPart.find(",") >= 0:
				cleanPart = '"%s"' % cleanPart
			partsWithCommasQuoted.append(cleanPart)
		else:
			partsWithCommasQuoted.append("")
	return ','.join(partsWithCommasQuoted) 

def caseInsensitiveFind(text, searchFor):
	return text.lower().find(searchFor.lower()) >= 0

# from http://www.letsyouandhimfight.com/2008/04/12/time-zones-in-google-app-engine/
# with a few changes
class TzDateTimeProperty(db.DateTimeProperty):
	def get_value_for_datastore(self, model_instance):
		value = super(TzDateTimeProperty, self).get_value_for_datastore(model_instance)
		if value:
			if value.tzinfo is None:
				value = value.replace(tzinfo=pytz.utc)
			else:
				value = value.astimezone(pytz.utc)
			return super(TzDateTimeProperty, self).get_value_for_datastore(model_instance)
		else:
			return None
	def make_value_from_datastore(self, value):
		value = super(TzDateTimeProperty, self).make_value_from_datastore(value)
		if value:
			if value.tzinfo is None:
				value = value.replace(tzinfo=pytz.utc)
			else:
				value = value.astimezone(pytz.utc)
		return value
	
class IdNumberDictionaryProperty(db.Property):
	data_type = str
	def get_value_for_datastore(self, model_instance):
		# for writing to datastore
		value = super(IdNumberDictionaryProperty, self).get_value_for_datastore(model_instance)
		if value is not None:
			textList = []
			for key in value:
				textList.append("%s|%s" % (key, value[key]))
			text = "@@@".join(textList)
			return text
		else:
			return None
	def make_value_from_datastore(self, value):
		# for reading from datastore
		if value is not None:
			dictionary = {}
			valueAsList = value.split("@@@")
			for listItem in valueAsList:
				key, content = listItem.split("|")
				dictionary[key] = int(content)
			return dictionary
		else:
			return {}
	def empty(self, value):
		return not value
	
# ============================================================================================
# ============================================================================================
class CounterShard(db.Model): 
# ============================================================================================
# to shard counters
# no parent
# ============================================================================================

	type = db.StringProperty(required=True)
	count = db.IntegerProperty(required=True, default=0, indexed=False)
	
# ============================================================================================
# ============================================================================================
class CounterShardConfiguration(db.Model): 
# ============================================================================================
# to define counter sharding
# no parent
# ============================================================================================

	type = db.StringProperty(required=True, indexed=False)
	numShards = db.IntegerProperty(required=True, default=20, indexed=False)
	
# ============================================================================================
# ============================================================================================
class Rakontu(db.Model): 
# ============================================================================================
# community or group
# no parent
# ============================================================================================

	# identification
	name = db.StringProperty(required=True) # appears on all pages at top
	
	# state
	active = db.BooleanProperty(default=True)
	created = TzDateTimeProperty(auto_now_add=True, indexed=False) 

	# governance options
	maxNumAttachments = db.IntegerProperty(choices=NUM_ATTACHMENT_CHOICES, default=DEFAULT_MAX_NUM_ATTACHMENTS, indexed=False)
	maxNudgePointsPerEntry = db.IntegerProperty(default=DEFAULT_MAX_NUDGE_POINTS_PER_ENTRY, indexed=False)
	memberNudgePointsPerEvent = db.ListProperty(int, default=DEFAULT_MEMBER_NUDGE_POINT_ACCUMULATIONS, indexed=False)
	nudgeCategories = db.StringListProperty(default=DEFAULT_NUDGE_CATEGORIES, indexed=False)
	nudgeCategoryQuestions = db.StringListProperty(default=DEFAULT_NUDGE_CATEGORY_QUESTIONS, indexed=False)
	entryActivityPointsPerEvent = db.ListProperty(int, default=DEFAULT_ARCTICLE_ACTIVITY_POINT_ACCUMULATIONS, indexed=False)
	allowCharacter = db.ListProperty(bool, default=DEFAULT_ALLOW_CHARACTERS, indexed=False)
	allowNonManagerCuratorsToEditTags = db.BooleanProperty(default=False, indexed=False)
	
	# descriptive options
	type = db.StringProperty(choices=RAKONTU_TYPES, default=RAKONTU_TYPES[-1], indexed=False) # only used to determine questions at front, but may be useful later so saving
	tagline = db.StringProperty(default="", indexed=False) # appears under name, optional
	image = db.BlobProperty(default=None) # appears on all pages, should be small (100x60 is best)
	contactEmail = db.StringProperty(default=DEFAULT_CONTACT_EMAIL, indexed=False) # sender address for emails sent from site
	
	description = db.TextProperty(default=DEFAULT_RAKONTU_DESCRIPTION) # appears on "about rakontu" page
	description_formatted = db.TextProperty() # formatted texts kept separate for re-editing original
	description_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	etiquetteStatement = db.TextProperty(default=DEFAULT_ETIQUETTE_STATEMENT) # appears on "about rakontu" page
	etiquetteStatement_formatted = db.TextProperty()
	etiquetteStatement_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	welcomeMessage = db.TextProperty(default=DEFAULT_WELCOME_MESSAGE) # appears only on new member welcome page
	welcomeMessage_formatted = db.TextProperty()
	welcomeMessage_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	roleReadmes = db.ListProperty(db.Text, default=[db.Text(DEFAULT_ROLE_READMES[0]), db.Text(DEFAULT_ROLE_READMES[1]), db.Text(DEFAULT_ROLE_READMES[2])])
	roleReadmes_formatted = db.ListProperty(db.Text, default=[db.Text(""), db.Text(""), db.Text("")])
	roleReadmes_formats = db.StringListProperty(default=DEFAULT_ROLE_READMES_FORMATS, indexed=False)
	
	# display options
	defaultTimeZoneName = db.StringProperty(default=DEFAULT_TIME_ZONE, indexed=False) # appears on member preferences page
	defaultTimeFormat = db.StringProperty(default=DEFAULT_TIME_FORMAT, indexed=False) # appears on member preferences page
	defaultDateFormat = db.StringProperty(default=DEFAULT_DATE_FORMAT, indexed=False) # appears on member preferences page
	skinName = db.StringProperty(default=DEFAULT_SKIN_NAME, indexed=False)
	customSkin = db.TextProperty(indexed=False)
	externalStyleSheetURL = db.StringProperty(default=None, indexed=False)

	def initializeFormattedTexts(self):
		self.description_formatted = db.Text("<p>%s</p>" % self.description)
		self.etiquetteStatement_formatted = db.Text("<p>%s</p>" % self.etiquetteStatement)
		self.welcomeMessage_formatted = db.Text("<p>%s</p>" % self.welcomeMessage)
		for i in range(3):
			self.roleReadmes_formatted[i] = db.Text(self.roleReadmes[i])
			
	def initializeCustomSkinText(self):
		skin = GetSkinByName(START_CUSTOM_SKIN_NAME)
		if skin:
			self.customSkin = db.Text(skin.asText())
	
	# OPTIONS
	
	def allowsAttachments(self):
		return self.maxNumAttachments > 0
	
	def allowsAtLeastTwoAttachments(self):
		return self.maxNumAttachments >= 2
	
	def allowsAtLeastThreeAttachments(self):
		return self.maxNumAttachments >= 3
	
	def allowsAtLeastFourAttachments(self):
		return self.maxNumAttachments >= 4
	
	def allowsFiveAttachments(self):
		return self.maxNumAttachments == 5
	
	def getSkinDictionary(self):
		if self.skinName == TERMS["term_custom"] and self.customSkin:
			return self.customSkinAsDictionary()
		elif self.skinName == TEMPLATE_TERMS["template_none"]:
			return {}
		else:
			skin = Skin.all().filter("name = ", self.skinName).get()
			if skin:
				return skin.getPropertiesAsDictionary()
			else:
				return {}
			
	def customSkinAsDictionary(self):
		result = {}
		rows = self.customSkin.split("\n")
		for row in rows:
			key = stringUpTo(row, "=")
			value = stringBeyond(row, "=")
			result[key] = value
		return result
	
	def nudgeCategoryIndexHasContent(self, index):
		return self.nudgeCategories[index] != None and self.nudgeCategories[index] != ""
		
	# DISPLAY
	
	def imageEmbed(self):
		return '<img src="/%s/%s?%s=%s" class="bordered">' % (DIRS["dir_visit"], URLS["url_image"], URL_IDS["url_query_rakontu"], self.getKeyName())
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s">%s</a>' % (self.linkURL(), self.name)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_home"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_rakontu"], self.key().name())

	# MEMBERS
	
	def getPendingMembers(self):
		return PendingMember.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)

	def getOfflineMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("isOnlineMember = ", False).fetch(FETCH_NUMBER)
	
	def getMemberNudgePointsForEvent(self, event):
		i = 0
		for eventType in EVENT_TYPES:
			if event == eventType:
				return self.memberNudgePointsPerEvent[i]
			i += 1
		return 0
	
	def getMemberForGoogleAccountId(self, id):
		return Member.all().filter("rakontu = ", self.key()).filter("googleAccountID = ", id).fetch(1)
		
	def getMembers(self):
		return Member.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
	
	def getActiveAndInactiveMembers(self):
		return Member.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
	
	def getActiveMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def getInactiveMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", False).fetch(FETCH_NUMBER)
	
	def getActiveOnlineMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", True).filter("isOnlineMember = ", True).fetch(FETCH_NUMBER)
	
	def getActiveOfflineMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", True).filter("isOnlineMember = ", False).fetch(FETCH_NUMBER)
	
	def getInactiveOfflineMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", False).filter("isOnlineMember = ", False).fetch(FETCH_NUMBER)
	
	def getActiveAndInactiveOfflineMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("isOnlineMember = ", False).fetch(FETCH_NUMBER)
	
	def numMembers(self):
		return Member.all().filter("rakontu = ", self.key()).count()
	
	def numActiveMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", True).count()
	
	def numPendingMembers(self):
		return PendingMember.all().filter("rakontu = ", self.key()).count()
		
	def numInactiveMembers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("active = ", False).count()
		
	def numEntries(self):
		return Entry.all().filter("rakontu = ", self.key()).count()
	
	def numNonDraftEntries(self):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).count()
	
	def numNonDraftEntriesOfType(self, type):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).filter("type = ", type).count()
	
	def hasNonDraftEntries(self):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).count() > 0
	
	def numAnnotations(self):
		# this is only used in the admin pages - documentation will say could be > 1000
		return Annotation.all().filter("rakontu = ", self.key()).count()
	
	def numAnswers(self):
		# this is only used in the admin pages - documentation will say could be > 1000
		return Answer.all().filter("rakontu = ", self.key()).count()
	
	def getGuides(self):
		result = []
		onlineMembers = Member.all().filter("rakontu = ", self.key()).filter("active = ", True).filter("isOnlineMember = ", True).fetch(FETCH_NUMBER)
		for member in onlineMembers:
			if member.isGuide():
				result.append(member)
		return result
	
	def getActiveOfflineMembersForLiaison(self, liaison):
		return Member.all().\
			filter("rakontu = ", self.key()).\
			filter("active = ", True).\
			filter("isOnlineMember = ", False).\
			filter("liaisonIfOfflineMember = ", liaison.key()).\
			fetch(FETCH_NUMBER)
	
	def getLiaisonsOtherThanMember(self, member):
		result = []
		onlineMembers = Member.all().filter("rakontu = ", self.key()).filter("active = ", True).filter("isOnlineMember = ", True).fetch(FETCH_NUMBER)
		for aMember in onlineMembers:
			if aMember.isLiaison() and aMember.key() != member.key():
				result.append(aMember)
		return result
	
	def hasMemberWithGoogleEmail(self, email):
		members = self.getActiveMembers()
		for member in members:
			if member.googleAccountEmail == email:
				return True
		return False
	
	def memberWithGoogleUserID(self, id):
		members = self.getActiveMembers()
		for member in members:
			if member.googleAccountID == id:
				return member
		return None
	
	def pendingMemberWithGoogleEmail(self, email):
		pendingMembers = self.getPendingMembers()
		for pendingMember in pendingMembers:
			if pendingMember.email == email:
				return pendingMember
		return None
	
	def memberWithNickname(self, nickname):
		members = self.getActiveAndInactiveMembers()
		for member in members:
			if member.nickname == nickname:
				return member
		return None
	
	def hasMemberWithNickname(self, nickname):
		members = self.getActiveAndInactiveMembers()
		for member in members:
			if member.nickname == nickname:
				return True
		return False
	
	def getOfflineMemberForNickname(self, nickname):
		members = self.getActiveAndInactiveOfflineMembers()
		for member in members:
			if member.nickname == nickname:
				return member
		return None
	
	def getManagers(self):
		return Member.all().filter("rakontu = ", self.key()).filter("governanceType = ", "manager").fetch(FETCH_NUMBER)
	
	def getOwners(self):
		return Member.all().filter("rakontu = ", self.key()).filter("governanceType = ", "owner").fetch(FETCH_NUMBER)
	
	def getManagersAndOwners(self):
		return Member.all().filter("rakontu = ", self.key()).filter("governanceType IN ", ["owner", "manager"]).fetch(FETCH_NUMBER)
	
	def memberIsOnlyOwner(self, member):
		owners = self.getOwners()
		if len(owners) == 1 and owners[0].key() == member.key():
			return True
		return False
	
	# CHARACTERS
	
	def getCharacters(self):
		return Character.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
	
	def getActiveCharacters(self):
		return Character.all().filter("rakontu = ", self.key()).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def getInactiveCharacters(self):
		return Character.all().filter("rakontu = ", self.key()).filter("active = ", False).fetch(FETCH_NUMBER)
	
	def hasAtLeastOneCharacterEntryAllowed(self, entryTypeIndex):
		return self.allowCharacter[entryTypeIndex] or len(self.getActiveCharacters()) > 0

	def hasActiveCharacters(self):
		return Character.all().filter("rakontu = ", self.key()).filter("active = ", True).count() > 0
	
	# ENTRIES
	
	def getNonDraftEntries(self):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getNonDraftEntriesOfTypeInReverseTimeOrder(self, type):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).filter("type = ", type).order("-published").fetch(FETCH_NUMBER)
	
	def browseEntries(self, minTime, maxTime, entryTypes):
		return Entry.all().filter("rakontu = ", self.key()).\
			filter("draft = ", False).\
			filter("type IN ", entryTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).\
			fetch(FETCH_NUMBER)
			
	def selectEntriesFromList(self, entries, minTime, maxTime, entryTypes):
		result = []
		for entry in entries:
			if entry.published and entry.published >= minTime and entry.published < maxTime and entry.type in entryTypes:
				result.append(entry)
		return result
	
	def getNonDraftEntriesOfType(self, type):
		return Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def getEntryActivityPointsForEvent(self, event):
		i = 0
		for eventType in EVENT_TYPES:
			if event == eventType:
				return self.entryActivityPointsPerEvent[i]
			i += 1
		return 0
	
	def getNonDraftNewMemberResourcesAsDictionaryByCategory(self):
		result = {}
		resources = Entry.all().filter("rakontu = ", self.key()). \
			filter("draft = ", False). \
			filter("type = ", "resource"). \
			filter("resourceForNewMemberPage =", True). \
			filter("resourceForManagersAndOwnersOnly = ", False). \
			fetch(FETCH_NUMBER)
		for resource in resources:
			if not result.has_key(resource.categoryIfResource):
				result[resource.categoryIfResource] = []
			result[resource.categoryIfResource].append(resource)
		for key in result.keys():
			result[key].sort(lambda a,b: cmp(a.orderIfResource, b.orderIfResource))
		return result
	
	def getNonDraftHelpResourcesAsDictionaryByCategory(self):
		result = {}
		resources = Entry.all().filter("rakontu = ", self.key()). \
			filter("draft = ", False). \
			filter("type = ", "resource"). \
			filter("resourceForHelpPage = ", True). \
			filter("resourceForManagersAndOwnersOnly = ", False). \
			fetch(FETCH_NUMBER)
		for resource in resources:
			if not result.has_key(resource.categoryIfResource):
				result[resource.categoryIfResource] = []
			result[resource.categoryIfResource].append(resource)
		for key in result.keys():
			result[key].sort(lambda a,b: cmp(a.orderIfResource, b.orderIfResource))
		return result
	
	def getNonDraftNewMemberManagerResourcesAsDictionaryByCategory(self):
		result = {}
		resources = Entry.all().filter("rakontu = ", self.key()). \
			filter("draft = ", False). \
			filter("type = ", "resource"). \
			filter("resourceForNewMemberPage =", True). \
			filter("resourceForManagersAndOwnersOnly = ", True). \
			fetch(FETCH_NUMBER)
		for resource in resources:
			if not result.has_key(resource.categoryIfResource):
				result[resource.categoryIfResource] = []
			result[resource.categoryIfResource].append(resource)
		for key in result.keys():
			result[key].sort(lambda a,b: cmp(a.orderIfResource, b.orderIfResource))
		return result
	
	def getNonDraftManagerOnlyHelpResourcesAsDictionaryByCategory(self):
		result = {}
		resources = Entry.all().filter("rakontu = ", self.key()). \
			filter("draft = ", False). \
			filter("type = ", "resource"). \
			filter("resourceForManagersAndOwnersOnly = ", True). \
			fetch(FETCH_NUMBER)
		for resource in resources:
			if not result.has_key(resource.categoryIfResource):
				result[resource.categoryIfResource] = []
			result[resource.categoryIfResource].append(resource)
		for key in result.keys():
			result[key].sort(lambda a,b: cmp(a.orderIfResource, b.orderIfResource))
		return result
	
	def getResourceWithTitle(self, title):
		return Entry.all().filter("rakontu = ", self.key()).filter("type = ", "resource").filter("title = ", title).get()
	
	def getResourceCategoryList(self):
		categoryDict = {}
		resources = Entry.all().filter("rakontu = ", self.key()). \
			filter("draft = ", False). \
			filter("type = ", "resource"). \
			fetch(FETCH_NUMBER)
		for resource in resources:
			if resource.categoryIfResource and not categoryDict.has_key(resource.categoryIfResource):
				categoryDict[resource.categoryIfResource] = 1
		result = categoryDict.keys()
		result.sort()
		return result
	
	# ENTRIES, ANNOTATIONS, ANSWERS, LINKS - EVERYTHING
	
	def getAllFlaggedItems(self):
		entries = Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).filter("flaggedForRemoval = ", True).fetch(FETCH_NUMBER)
		annotations = Annotation.all().filter("rakontu = ", self.key()).filter("flaggedForRemoval = ", True).fetch(FETCH_NUMBER)
		answers = Answer.all().filter("rakontu = ", self.key()).filter("flaggedForRemoval = ", True).fetch(FETCH_NUMBER)
		links = Link.all().filter("rakontu = ", self.key()).filter("flaggedForRemoval = ", True).fetch(FETCH_NUMBER)
		searches = SavedSearch.all().filter("rakontu = ", self.key()).filter("flaggedForRemoval = ", True).fetch(FETCH_NUMBER)
		return (entries, annotations, answers, links, searches)
	
	def getAllFlaggedItemsAsOneList(self):
		result = []
		(entries, annotations, answers, links, searches) = self.getAllFlaggedItems()
		result.extend(links)
		result.extend(answers)
		result.extend(annotations)
		result.extend(entries)
		result.extend(searches)
		return result

	def getAllItems(self):
		entries = Entry.all().filter("rakontu = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
		annotations = Annotation.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
		answers = Answer.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
		links = Link.all().filter("rakontu = ", self.key()).filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
		return (entries, annotations, answers, links)
	
	def getAllEntriesAnnotationsAndAnswersAsOneList(self):
		result = []
		(entries, annotations, answers, links) = self.getAllItems()
		result.extend(entries)
		result.extend(answers)
		result.extend(annotations)
		return result
	
	def hasTheMaximumNumberOfEntries(self):
		numEntriesIncludingDrafts = Entry.all().filter("rakontu = ", self.key()).count()
		return numEntriesIncludingDrafts >= MAX_ENTRIES_PER_RAKONTU
	
	def hasWithinTenOfTheMaximumNumberOfEntries(self):
		numEntriesIncludingDrafts = Entry.all().filter("rakontu = ", self.key()).count()
		return numEntriesIncludingDrafts >= MAX_ENTRIES_PER_RAKONTU - 10

	def getEntryInImportBufferWithTitle(self, title):	
		return Entry.all().filter("rakontu = ", self.key()).filter("inBatchEntryBuffer = ", True).filter("title = ", title).get()
										
	def getEntriesInImportBufferForLiaison(self, liaison):
		return Entry.all().filter("rakontu = ", self.key()).filter("inBatchEntryBuffer = ", True).filter("liaison = ", liaison.key()).fetch(FETCH_NUMBER)
	
	def getCommentsInImportBufferForLiaison(self, liaison):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "comment").filter("inBatchEntryBuffer = ", True).filter("liaison = ", liaison.key()).fetch(FETCH_NUMBER)
		
	def getTagsetsInImportBufferForLiaison(self, liaison):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "tag set").filter("inBatchEntryBuffer = ", True).filter("liaison = ", liaison.key()).fetch(FETCH_NUMBER)
		
	def getAllRequests(self):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "request").fetch(FETCH_NUMBER)
		
	def getAllRequestsOfType(self, type):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "request").\
			filter("typeIfRequest = ", type).fetch(FETCH_NUMBER)
		
	def getAllUncompletedRequestsOfType(self, type):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "request").\
				filter("typeIfRequest = ", type).filter("completedIfRequest = ", False).fetch(FETCH_NUMBER)
	
	def getTagSets(self):
		return Annotation.all().filter("rakontu = ", self.key()).filter("type = ", "tag set").fetch(FETCH_NUMBER)
	
	def getTags(self):
		tags = {}
		tagsets = self.getTagSets()
		for tagset in tagsets:
			for tag in tagset.tagsIfTagSet:
				tags[tag] = 1
		tagsSorted = []
		tagsSorted.extend(tags.keys())
		tagsSorted.sort()
		return tagsSorted
			
	def getCounts(self):
		countNames = []
		counts = []
		i = 0
		for aType in ENTRY_TYPES:
			countNames.append(ENTRY_TYPES_PLURAL_DISPLAY[i])
			count = Entry.all().filter("rakontu = ", self.key()).filter("type = ", aType).count()
			counts.append(count)
			i += 1
		i = len(ENTRY_TYPES)
		j = 0
		for aType in ANNOTATION_ANSWER_LINK_TYPES:
			if aType in ANNOTATION_TYPES:
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Annotation.all().filter("rakontu = ", self.key()).filter("type = ", aType).count()
				counts.append(count)
			elif aType == "answer":
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Answer.all().filter("rakontu = ", self.key()).count()
				counts.append(count)
			elif aType == "link":
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Link.all().filter("rakontu = ", self.key()).count()
				counts.append(count)
			i += 1
			j += 1
		return countNames, counts
	
	# QUERIES WITH PAGING
	
	def getNonDraftEntriesLackingMetadata_WithPaging(self, show, type, sortBy, bookmark, numToFetch=MAX_ITEMS_PER_LIST_PAGE):
		query = pager.PagerQuery(Entry).filter("rakontu = ", self.key()).filter("draft = ", False).filter("type = ", type).order("-__key__")
		prev, entries, next = query.fetch(numToFetch, bookmark)
		result = []
		for entry in entries:
			doNotAdd = True
			if show == "entries_no_tags":
				doNotAdd = entry.hasTagSets()
			elif show == "entries_no_links":
				doNotAdd =  entry.hasLinks()
			elif show == "entries_no_comments":
				doNotAdd =  entry.hasComments()
			elif show == "entries_no_answers":
				doNotAdd =  entry.hasAnswers()
			elif show == "collages_no_links":
				doNotAdd =  (not entry.isCollage()) or entry.hasOutgoingLinksOfType("included")
			elif show == "invitations_no_resopnses":
				doNotAdd = (not entry.isInvitation()) or entry.hasOutgoingLinksOfType("responded")
			if not doNotAdd:
				result.append(entry)
		if sortBy == "activity":
			result.sort(lambda a,b: cmp(b.activityPoints, a.activityPoints))
		elif sortBy == "nudges":
			result.sort(lambda a,b: cmp(b.nudgePointsCombined(), a.nudgePointsCombined()))
		elif sortBy == "date":
			result.sort(lambda a,b: cmp(b.published, a.published))
		elif sortBy == "annotations":
			result.sort(lambda a,b: cmp(b.getAnnotationCount(), a.getAnnotationCount()))
		return prev, result, next
	
	def getAttachments_WithPaging(self, bookmark, numToFetch=MAX_ITEMS_PER_LIST_PAGE):
		# note, cannot get this to work with date order, using key order instead
		# wants FixedOffset class, which is here
		# http://docs.python.org/library/datetime.html#datetime-tzinfo
		# but can't load it ??
		query = pager.PagerQuery(Attachment).filter("rakontu = ", self.key()).order("-__key__")
		prev, results, next = query.fetch(numToFetch, bookmark)
		return prev, results, next
	
	def getTagSets_WithPaging(self, bookmark, numToFetch=MAX_ITEMS_PER_LIST_PAGE):
		query = pager.PagerQuery(Annotation).filter("rakontu = ", self.key()).filter("type = ", "tag set").order("-__key__")
		prev, results, next = query.fetch(numToFetch, bookmark)
		return prev, results, next
	
	def getNonDraftEntriesOfType_WithPaging(self, type, bookmark, numToFetch=MAX_ITEMS_PER_LIST_PAGE):
		query = pager.PagerQuery(Entry).filter("rakontu = ", self.key()).filter("draft = ", False).filter("type = ", type).order("-__key__")
		return query.fetch(numToFetch, bookmark)
	
	# QUESTIONS
	
	def getAllQuestions(self):
		return Question.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
	
	def getAllQuestionsOfReferType(self, type):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo = ", type).fetch(FETCH_NUMBER)
	
	def getActiveQuestions(self):
		return Question.all().filter("rakontu = ", self.key()).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def getActiveQuestionsOfType(self, type):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo = ", type).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def getInactiveQuestionsOfType(self, type):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo = ", type).filter("active = ", False).fetch(FETCH_NUMBER)
	
	def getQuestionsOfType(self, type):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo = ", type).fetch(FETCH_NUMBER)
	
	def getActiveMemberQuestions(self):
		return self.getActiveQuestionsOfType("member")
	
	def getActiveNonMemberNonCharacterQuestions(self):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo !=", "member").filter("refersTo !=", "character").filter("active = ", True).fetch(FETCH_NUMBER)
		
	def getActiveMemberAndCharacterQuestions(self):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo IN ", ["character", "member"]).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def hasActiveQuestionsOfType(self, type):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo = ", type).filter("active = ", True).count() > 0
	
	def hasActiveNonMemberQuestions(self):
		return Question.all().filter("rakontu = ", self.key()).filter("refersTo !=", "member").filter("active = ", True).count() > 0
		
	def hasQuestionWithSameTypeAndName(self, question):
		allQuestions = self.getAllQuestions()
		for aQuestion in allQuestions:
			if aQuestion.refersTo == question.refersTo and aQuestion.name == question.name:
				return True
		return False
	
	def GenerateCopyOfQuestion(self, question):
		keyName = GenerateSequentialKeyName("question")
		newQuestion = Question(
							   key_name=keyName,
							   parent=self,
							   id=keyName,
							   rakontu=self,
							   refersTo=question.refersTo,
							   name=question.name,
							   text=question.text,
							   type=question.type,
							   choices=question.choices,
							   multiple=question.multiple,
							   help=question.help,
							   useHelp=question.useHelp)
		return newQuestion # caller will do the put
		
	def GenerateQuestionsOfTypeFromCSV(self, type, input):
		rows = csv.reader(input.split("\n"))
		result = []
		for row in rows:
			if len(row) >= 4 and row[0] and row[1] and row[0][0] != ";":
				refersTo = row[0].strip()
				if not refersTo in QUESTION_REFERS_TO:
					continue
				name = row[1]
				text = row[2]
				type = row[3]
				choices = []
				minValue = DEFAULT_QUESTION_VALUE_MIN
				maxValue = DEFAULT_QUESTION_VALUE_MAX
				responseIfBoolean = DEFAULT_QUESTION_BOOLEAN_RESPONSE
				if type == "ordinal" or type == "nominal":
					choices = [x.strip() for x in row[4].split(",")]
				elif type == "value":
					minAndMax = row[4].split("-")
					try:
						minValue = int(minAndMax[0])
					except:
						pass
					try:
						maxValue = int(minAndMax[1])
					except:
						pass
				elif type == "boolean":
					responseIfBoolean = row[4]
				multiple = row[5] == "yes"
				help = row[6]
				useHelp=row[7]
				keyName = GenerateSequentialKeyName("question")
				question = Question(
								key_name=keyName,
								parent=self,
								id=keyName,
								rakontu=self,
								refersTo=refersTo, 
								name=name, 
								text=text, 
								type=type, 
								choices=choices, 
								multiple=multiple,
								responseIfBoolean=responseIfBoolean, 
								minIfValue=minValue, 
								maxIfValue=maxValue, 
								help=help, 
								useHelp=useHelp, 
								)
				result.append(question)
		return result
		
	# SEARCHES
	
	def getNonPrivateSavedSearches(self):
		return SavedSearch.all().filter("rakontu = ", self.key()).filter("private = ", False).fetch(FETCH_NUMBER)
		
	# REMOVAL
	
	def removeAllDependents(self):
		# kludgy, but keep removing entries until there aren't any more
		while 1:
			entries = Entry.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER)
			if not entries:
				break
			else:
				for entry in entries:
					entry.removeAllDependents()
				db.delete(entries)
		for member in self.getMembers():
			member.removeAllDependents()
		db.delete(SavedSearch.all().filter("rakontu =", self.key()).fetch(FETCH_NUMBER)) # shared searches
		db.delete(Member.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER))
		db.delete(PendingMember.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER))
		for character in self.getCharacters():
			character.removeAllDependents()
		db.delete(Character.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER))
		db.delete(Question.all().filter("rakontu = ", self.key()).fetch(FETCH_NUMBER))
		
	# IMPORT
	
	def addEntriesFromCSV(self, data, liaison):
		reader = csv.reader(data.split("\n"), delimiter=',', doublequote='"', quotechar='"')
		for row in reader:
			dateOkay = True
			if len(row) > 0 and len(row[0]) > 0 and row[0][0] != ";" and row[0][0] != "#":
				nickname = row[0].strip()
				member = self.memberWithNickname(nickname)
				if member:
					if liaison.isManagerOrOwner() or member.liaisonIfOfflineMember.key() == liaison.key():
						if len(row) >= 1:
							dateString = row[1].strip()
						else:
							dateString = None
							dateOkay = False
						if dateOkay:
							try:
								(year, month, day) = dateString.split("-")
							except:
								dateOkay = False
							if dateOkay:
								try:
									collected = datetime(int(year), int(month), int(day))
								except:
									collected = None
									dateOkay = False
								if dateOkay:
									if len(row) >= 3:
										type = row[2].strip()
									else:
										type = None
									typeOkay = type in ENTRY_TYPES # NOTE: does not allow translated name
									if type and typeOkay:
										if len(row) >= 4:
											title = row[3].strip()
										else:
											title = None
										if title:
											foundEntry = self.getEntryInImportBufferWithTitle(title)
											if not foundEntry:
												if len(row) >= 5:
													text = row[4].strip()
												else:
													text = "No text imported."
												keyName = GenerateSequentialKeyName("entry")
												entry = Entry(key_name=keyName, parent=member, id=keyName, rakontu=self, type=type, title=title) 
												entry.text = text
												entry.rakontu = self
												entry.creator = member
												entry.collectedOffline = True
												entry.collected = collected
												entry.liaison = liaison
												entry.inBatchEntryBuffer = True
												entry.draft = True
												entry.put()	
		
	# EXPORT
	
	def getExportOfType(self, type):
		return Export.all().filter("rakontu = ", self.key()).filter("type = ", type).get()

	def createOrRefreshExport(self, type, subtype, member=None, entry=None, startNumber=None, endNumber=None, memberToSee=None, character=None, questionType=None, fileFormat="csv"):
		exportAlreadyThereForType = self.getExportOfType(type)
		if exportAlreadyThereForType:
			db.delete(exportAlreadyThereForType)
		export = Export(key_name=GenerateSequentialKeyName("export"), rakontu=self, type=type, fileFormat=fileFormat)
		exportText = ""
		if type == "csv_export_search":
			if member:
				exportText += '"Export of viewed items for member "%s" in Rakontu %s"\n' % (member.nickname, self.name)
				(entries, overLimitWarning, numItemsBeforeLimitTruncation) = ItemsMatchingViewOptionsForMemberAndLocation(member, "home")
				if overLimitWarning:
					exportText += '\n"%s of %s %s\n"' % (MAX_ITEMS_PER_GRID_PAGE, numItemsBeforeLimitTruncation, overLimitWarning)
				memberQuestions = self.getActiveQuestionsOfType("member")
				characterQuestions = self.getActiveQuestionsOfType("character")
				typeCount = 0
				for type in ENTRY_TYPES:
					entriesOfThisType = []
					for entry in entries:
						if entry.type == type:
							entriesOfThisType.append(entry)
					if entriesOfThisType:
						questions = self.getActiveQuestionsOfType(type)
						exportText += '\n%s\nTitle,Date,Text,Contributor,' % ENTRY_TYPES_PLURAL_DISPLAY[typeCount].upper()
						for question in questions:
							exportText += question.name + ","
						for question in memberQuestions:
							exportText += question.name + ","
						for question in characterQuestions:
							exportText += question.name + ","
						exportText += '\n'
						i = 0
						for entry in entriesOfThisType:
							exportText += entry.csvLineWithAnswers(member, questions, memberQuestions, characterQuestions) 
							i += 1
					typeCount += 1
		elif type == "csv_export_all":
			exportText += '"%s export for Rakontu %s"\n' % (subtype.capitalize(), self.name)
			memberQuestions = self.getActiveQuestionsOfType("member")
			characterQuestions = self.getActiveQuestionsOfType("character")
			questions = self.getActiveQuestionsOfType(subtype)
			entries = self.getNonDraftEntriesOfTypeInReverseTimeOrder(subtype)
			exportText += '\n%s\nTitle,Date,Text,Contributor,' % subtype.upper()
			for question in questions:
				exportText += question.name + ","
			for question in memberQuestions:
				exportText += question.name + ","
			for question in characterQuestions:
				exportText += question.name + ","
			exportText += '\n'
			for i in range(len(entries)):
				if (not startNumber and not endNumber) or (i >= startNumber and i < endNumber):
					exportText += entries[i].csvLineWithAnswers(member, questions, memberQuestions, characterQuestions) 
		elif type == "xml_export":
			if subtype == "rakontu":
				exportText += self.to_xml()
				for character in self.getActiveCharacters():
					exportText += character.to_xml() + "\n\n"
				for type in QUESTION_REFERS_TO:
					for question in self.getActiveQuestionsOfType(type):
						exportText += question.to_xml() + "\n\n"
				for search in self.getNonPrivateSavedSearches():
					exportText += search.to_xml() + "\n\n"
					for searchRef in search.getQuestionReferences():
						exportText += searchRef.to_xml() + "\n\n"
			elif subtype == "members":
				i = 0
				for member in self.getActiveMembers():
					if (not startNumber and not endNumber) or (i >= startNumber and i < endNumber):
						exportText += member.to_xml() + "\n\n"
					i += 1
				for pendingMember in self.getPendingMembers(): # these are tiny
					exportText += pendingMember.to_xml() + "\n\n"
			else:
				i = 0
				for entry in self.getNonDraftEntriesOfTypeInReverseTimeOrder(subtype):
					if (not startNumber and not endNumber) or (i >= startNumber and i < endNumber):
						exportText += entry.to_xml() + "\n\n"
						for attachment in entry.getAttachments():
							exportText += attachment.to_xml() + "\n\n"
						for annotation in entry.getAnnotations():
							exportText += annotation.to_xml() + "\n\n"
						for answer in entry.getAnswers():
							exportText += answer.to_xml() + "\n\n"
						for link in entry.getAllLinks():
							exportText += link.to_xml() + "\n\n"
							
					i += 1
		elif type == "liaisonPrint_simple":
			exportText += '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
			exportText += '<title>%s</title></head><body>' % TERMS["term_printed_from_rakontu"]
			if subtype == "search":
				exportText += "<h3>%s %s</h3>" % (TERMS["term_selections_for"], self.name)
				(entries, overLimitWarning, numItemsBeforeLimitTruncation) = ItemsMatchingViewOptionsForMemberAndLocation(member, "home")
				if overLimitWarning:
					exportText += '\n%s of %s %s\n' % (MAX_ITEMS_PER_GRID_PAGE, numItemsBeforeLimitTruncation, overLimitWarning)
				for entry in entries:
					exportText += entry.PrintText(member)
			elif subtype == "entry":
				exportText += "<h3>%s %s</h3>" % (TERMS["term_selections_for"], entry.title)
				(items, overLimitWarning, numItemsBeforeLimitTruncation) = ItemsMatchingViewOptionsForMemberAndLocation(member, "entry", entry=entry)
				if overLimitWarning:
					exportText += '\n%s of %s %s\n' % (MAX_ITEMS_PER_GRID_PAGE, numItemsBeforeLimitTruncation, overLimitWarning)
				else:
					items.insert(0, entry)
				for item in items:
					exportText += item.PrintText(member)
			elif subtype == "member":
				exportText += "<h3>%s %s</h3>" % (TERMS["term_selections_for"], memberToSee.nickname)
				(items, overLimitWarning, numItemsBeforeLimitTruncation) = ItemsMatchingViewOptionsForMemberAndLocation(member, "member", memberToSee=memberToSee)
				if overLimitWarning:
					exportText += '\n%s of %s %s\n' % (MAX_ITEMS_PER_GRID_PAGE, numItemsBeforeLimitTruncation, overLimitWarning)
				for item in items:
					exportText += item.PrintText(member)
			elif subtype == "character":
				exportText += "<h3>%s %s</h3>" % (TERMS["term_selections_for"], character.name)
				(items, overLimitWarning, numItemsBeforeLimitTruncation) = ItemsMatchingViewOptionsForMemberAndLocation(member, "character", character=character)
				if overLimitWarning:
					exportText += '\n%s of %s %s\n' % (MAX_ITEMS_PER_GRID_PAGE, numItemsBeforeLimitTruncation, overLimitWarning)
				for item in items:
					exportText += item.PrintText(member)
			exportText += "</body></html>"
		elif type == "exportQuestions":
			exportText += '; refersTo,name,text,type,choices or min-max or boolean "yes" text,multiple,help,help for using\n'
			questions = self.getActiveQuestionsOfType(questionType)
			for question in questions:
				cells = []
				cells.append(question.refersTo)
				cells.append(question.name)
				cells.append(question.text)
				cells.append(question.type)
				if question.type == "nominal" or question.type == "ordinal":
					choicesToReport = []
					for choice in question.choices:
						if len(choice):
							choicesToReport.append(choice)
					cells.append(", ".join(choicesToReport))
				elif question.type == "value":
					cells.append("%s-%s" % (question.minIfValue, question.maxIfValue))
				elif question.type == "boolean":
					cells.append(question.responseIfBoolean)
				else:
					cells.append("")
				if question.multiple:
					cells.append("yes")
				else:
					cells.append("no")
				cells.append(question.help)
				cells.append(question.useHelp)
				exportText += CleanUpCSV(cells) + "\n"
		export.data = db.Text(exportText)
		export.put()
		return export
		
# ============================================================================================
# ============================================================================================
class Question(db.Model):
# ============================================================================================
# thing asked about entry, member or character
# parent: rakontu; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	rakontu = db.ReferenceProperty(Rakontu, collection_name="questions_to_rakontu") 
	refersTo = db.StringProperty(choices=QUESTION_REFERS_TO, required=True)
	
	name = db.StringProperty(required=True, default=DEFAULT_QUESTION_NAME)
	text = db.StringProperty(required=True, indexed=False)
	type = db.StringProperty(choices=QUESTION_TYPES, default="text") # text, boolean, ordinal, nominal, value
	order = db.IntegerProperty(default=0) # order in list (for each type)
	
	active = db.BooleanProperty(default=True) # used to hide questions no longer being used, same as members
	
	minIfValue = db.IntegerProperty(default=DEFAULT_QUESTION_VALUE_MIN, indexed=False)
	maxIfValue = db.IntegerProperty(default=DEFAULT_QUESTION_VALUE_MAX, indexed=False)
	responseIfBoolean = db.StringProperty(default=DEFAULT_QUESTION_BOOLEAN_RESPONSE, indexed=False) # what the checkbox label should say
	multiple = db.BooleanProperty(default=False) # whether multiple answers are allowed (for ordinal/nominal only)
	choices = db.StringListProperty(default=[""] * MAX_NUM_CHOICES_PER_QUESTION, indexed=False) 
	
	help = db.TextProperty() # appears to person answering question
	help_formatted = db.TextProperty()
	help_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	useHelp = db.TextProperty() # appears to manager choosing question, about when to use it
	useHelp_formatted = db.TextProperty()
	useHelp_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	created = TzDateTimeProperty(auto_now_add=True)
	
	inBatchEntryBuffer = db.BooleanProperty(default=False) # in the process of being imported, not "live" yet
	
	def isOrdinalOrNominal(self):
		return self.type == "ordinal" or self.type == "nominal"
	
	def isTextOrValue(self):
		return self.type == "text" or self.type == "value"
	
	def numChoices(self):
		return len(self.choices)

	def refersToEntryType(self):
		return self.refersTo == "story" \
			or self.refersTo == "pattern" \
			or self.refersTo == "collage" \
			or self.refersTo == "invitation" \
			or self.refersTo == "resource" 
			
	def refersToMemberOrCharacter(self):
		return self.refersTo == "member" or self.refersTo == "character"
	
	def keyAsString(self):
		return "%s" % self.key()
	
	def getAnswerCount(self):
		return Answer.all().filter("question = ", self.key()).count()
			
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s">%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.text)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_manage"], URLS["url_question"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_question"], self.key().name())
	
	def choicesAsLineDelimitedTextString(self):
		return "\n".join(self.choices)
	
# ============================================================================================
# ============================================================================================
class Member(db.Model): 
# ============================================================================================
# person in rakontu
# parent: rakontu; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="members_to_rakontu")
	nickname = db.StringProperty(default=NO_NICKNAME_SET)
	isOnlineMember = db.BooleanProperty(default=True)
	liaisonIfOfflineMember = db.SelfReferenceProperty(default=None, collection_name="offline_members_to_liaisons")
	googleAccountID = db.StringProperty() # none if off-line member
	googleAccountEmail = db.StringProperty() # blank if off-line member
	
	# active: members are never removed, just inactivated, so entries can still link to something.
	# inactive members do not show up in any display, but they can be "reactivated" by issuing an invitation
	# to the same google email as before.
	active = db.BooleanProperty(default=True) 
	
	governanceType = db.StringProperty(choices=GOVERNANCE_ROLE_TYPES, default="member") # can only be set by managers
	helpingRoles = db.ListProperty(bool, default=[False, False, False], indexed=False) # members can choose
	helpingRolesAvailable = db.ListProperty(bool, default=[True, True, True], indexed=False) # managers can ban members from roles
	
	guideIntro = db.TextProperty(default=DEFAULT_GUIDE_INTRO) # appears on the welcome and get help pages if the member is a guide
	guideIntro_formatted = db.TextProperty()
	guideIntro_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	profileText = db.TextProperty(default=NO_PROFILE_TEXT)
	profileText_formatted = db.TextProperty()
	profileText_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	profileImage = db.BlobProperty(default=None) # optional, resized to 100x60
	acceptsMessages = db.BooleanProperty(default=True, indexed=False) # other members can send emails to their google email (without seeing it)
	messageReplyToEmail = db.StringProperty(default="", indexed=False)
	preferredTextFormat = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	shortDisplayLength = db.IntegerProperty(default=DEFAULT_DETAILS_TEXT_LENGTH) # how long to show texts in details
	
	viewOptions = db.ListProperty(db.Key)
	timeZoneName = db.StringProperty(default=DEFAULT_TIME_ZONE, indexed=False) # members choose these in their prefs page
	timeFormat = db.StringProperty(default=DEFAULT_TIME_FORMAT, indexed=False) # how they want to see dates
	dateFormat = db.StringProperty(default=DEFAULT_DATE_FORMAT, indexed=False) # how they want to see times
	showAttachedImagesInline = db.BooleanProperty(default=False, indexed=False)
	
	joined = TzDateTimeProperty(auto_now_add=True)
	firstVisited = db.DateTimeProperty(indexed=False)
	nudgePoints = db.IntegerProperty(default=DEFAULT_START_NUDGE_POINTS, indexed=False) # accumulated through participation
	
	# CREATION
	
	def initialize(self):
		self.timeZoneName = self.rakontu.defaultTimeZoneName
		self.timeFormat = self.rakontu.defaultTimeFormat
		self.dateFormat = self.rakontu.defaultDateFormat
		self.profileText_formatted = db.Text("<p>%s</p>" % self.profileText)
		self.guideIntro_formatted = db.Text("<p>%s</p>" % self.guideIntro)
		# caller does put
		
	def createViewOptions(self):
		viewOptionsNow = ViewOptions.all().ancestor(self)
		if viewOptionsNow:
			db.delete(viewOptionsNow)
		newObjects = []
		for location in VIEW_OPTION_LOCATIONS:
			# because the view options are never used in a URL query, they don't need a key name
			viewOptions = ViewOptions(parent=self, member=self, rakontu=self.rakontu, location=location)
			if viewOptions.endTime.tzinfo is None:
				viewOptions.endTime = viewOptions.endTime.replace(tzinfo=pytz.utc)
			newObjects.append(viewOptions)
		db.put(newObjects)
		self.viewOptions = []
		for option in newObjects:
			self.viewOptions.append(option.key())
		self.put()
		
	def removeAllDependents(self):
		db.delete(ViewOptions.all().filter("member = ", self.key()).fetch(8) )
		db.delete(Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER))
		searches = self.getPrivateSavedSearches()
		for search in searches:
			search.removeAllDependents()
		db.delete(searches)
	
	def getAllViewOptions(self):
		return ViewOptions.all().ancestor(self).fetch(FETCH_NUMBER)
		
	# INFO
	
	def isMember(self):
		return True
		
	def googleUserEmailOrNotOnline(self):
		if self.isOnlineMember:
			return self.googleAccountEmail
		return "%s (%s)" % (TERMS["term_none"], TEMPLATE_TERMS["template_offline"])
	
	# GOVERNANCE
	
	def isRegularMember(self):
		return self.governanceType == "member"
	
	def isManager(self):
		return self.governanceType == "manager"
	
	def isOwner(self):
		return self.governanceType == "owner"
	
	def isManagerOrOwner(self):
		return self.governanceType == "manager" or self.governanceType == "owner"
	
	def governanceTypeForDisplay(self):
		# GOVERNANCE_ROLE_TYPES_DISPLAY = ["member", "manager", "owner"]
		if self.governanceType == "member":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[0]
		elif self.governanceType == "manager":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[1]
		elif self.governanceType == "owner":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[2]
	
	def governanceTypeForDisplayNotShowingOwner(self):
		# GOVERNANCE_ROLE_TYPES_DISPLAY = ["member", "manager", "owner"]
		if self.governanceType == "member":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[0]
		elif self.governanceType == "manager":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[1]
		elif self.governanceType == "owner":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[1]
	
	# HELPING ROLES
	
	def isCurator(self):
		return self.helpingRoles[0]
	
	def isGuide(self):
		return self.helpingRoles[1]
	
	def isLiaison(self):
		return self.helpingRoles[2]
	
	def isCuratorOrManagerOrOwner(self):
		return self.isCurator() or self.isManagerOrOwner()
	
	def isGuideOrManagerOrOwner(self):
		return self.isGuide() or self.isManagerOrOwner()
	
	def isLiaisonOrManagerOrOwner(self):
		return self.isLiaison() or self.isManagerOrOwner()
	
	def hasAnyHelpingRole(self):
		return self.helpingRoles[0] or self.helpingRoles[1] or self.helpingRoles[2]

	def helpingRolesForDisplay(self):
		result = []
		if self.helpingRoles[0]:
			result.append(HELPING_ROLE_TYPES_DISPLAY[0])
		if self.helpingRoles[1]:
			result.append(HELPING_ROLE_TYPES_DISPLAY[1])
		if self.helpingRoles[2]:
			result.append(HELPING_ROLE_TYPES_DISPLAY[2])
		return result

	def canTakeOnAnyHelpingRole(self):
		return self.helpingRolesAvailable[0] or self.helpingRolesAvailable[1] or self.helpingRolesAvailable[2]
	
	def canEditTags(self):
		return (NUM_TAGS_IN_TAG_SET) and (self.isCurator() and self.isManagerOrOwner()) or (self.isCurator() and self.rakontu.allowNonManagerCuratorsToEditTags)
	
	# BROWSING - VIEW OPTIONS 
	
	def getViewOptionsForLocation(self, location):
		if not self.viewOptions:
			self.createViewOptions()
		if location == "home":
			return ViewOptions.get(self.viewOptions[0])
		elif location == "entry":
			return ViewOptions.get(self.viewOptions[1])
		elif location == "member":
			return ViewOptions.get(self.viewOptions[2])
		elif location == "character":
			return ViewOptions.get(self.viewOptions[3])
	
	def getAnnotationAnswerLinkTypeForLocationAndIndex(self, location, index):
		viewOptions = self.getViewOptionsForLocation(location)
		return viewOptions.annotationAnswerLinkTypes[index]
			
	def getEntryTypeForLocationAndIndex(self, location, index):
		viewOptions = self.getViewOptionsForLocation(location)
		return viewOptions.entryTypes[index]
	
	def firstVisitURL(self):
		if self.isManagerOrOwner():
			return BuildURL("dir_manage", "url_first", rakontu=self.rakontu)
		else:
			return BuildURL("dir_visit", "url_new", rakontu=self.rakontu)
		
	# CONTRIBUTIONS
	
	def getAllItemsAttributedToMember(self):
		result = []
		result.extend(self.getNonDraftEntriesAttributedToMember())
		result.extend(self.getAnnotationsAttributedToMember())
		result.extend(self.getAnswersAboutEntriesAttributedToMember())
		result.extend(self.getLinksCreatedByMember())
		return result
	
	def browseItems(self, minTime, maxTime, entryTypes, annotationTypes):
		result = []
		entries = Entry.all().filter("creator = ", self.key()).filter("draft = ", False).filter("character = ", None).\
			filter("type IN ", entryTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
		result.extend(entries)
		annotations = Annotation.all().filter("creator = ", self.key()).filter("character = ", None).\
			filter("type IN ", annotationTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
		result.extend(annotations)
		if "answer" in annotationTypes:
			answers = Answer.all().filter("creator = ", self.key()).filter("character = ", None).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(answers)
		if "link" in annotationTypes:
			links = Link.all().filter("creator = ", self.key()).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(links)
		return result
	
	def selectItemsFromList(self, items, minTime, maxTime, entryTypes, annotationTypes):
		result = []
		for item in items:
			if item.published and item.published >= minTime and item.published <= maxTime:
				if item.__class__.__name__ == "Entry":
					if item.type in entryTypes:
						result.append(item)
				elif item.__class__.__name__ == "Annotation":
					if item.type in annotationTypes:
						result.append(item)
				elif item.__class__.__name__ == "Answer":
					if "answer" in annotationTypes:
						result.append(item)
				elif item.__class__.__name__ == "Link":
					if "link" in annotationTypes:
						result.append(item)
		return result
	
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
	
	def getAnswerForQuestion(self, question):
		return Answer.all().filter("referent = ", self.key()).filter("question = ", question.key()).get()
	
	def getAnswerForMemberQuestion(self, question):
		return Answer.all().filter("question = ", question.key()).filter("referent =", self.key()).get()
	
	def getNonDraftEntriesAttributedToMember(self):
		return Entry.all().filter("creator = ", self.key()).filter("draft = ", False).filter("character = ", None).fetch(FETCH_NUMBER)
	
	def getAnnotationsAttributedToMember(self):
		return Annotation.all().filter("creator = ", self.key()).filter("character = ", None).fetch(FETCH_NUMBER)
	
	def getAnswersAboutEntriesAttributedToMember(self):
		return Answer.all().filter("creator = ", self.key()).filter("character = ", None).filter("referentType = ", "entry").fetch(FETCH_NUMBER)
	
	def getNonDraftLiaisonedEntries(self):
		return Entry.all().filter("liaison = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getLinksCreatedByMember(self):
		return Link.all().filter("creator = ", self.key()).fetch(FETCH_NUMBER)

	def getDraftEntries(self):
		return Entry.all().filter("creator = ", self.key()).filter("draft = ", True).fetch(FETCH_NUMBER)
	
	def getSavedSearches(self):
		return SavedSearch.all().filter("creator = ", self.key()).fetch(FETCH_NUMBER)
	
	def getPrivateSavedSearches(self):
		return SavedSearch.all().filter("creator = ", self.key()).filter("private = ", True).fetch(FETCH_NUMBER)
	
	def getCounts(self):
		countNames = []
		counts = []
		i = 0
		for aType in ENTRY_TYPES:
			countNames.append(ENTRY_TYPES_PLURAL_DISPLAY[i])
			count = Entry.all().filter("creator = ", self.key()).filter("character = ", None).filter("type = ", aType).count()
			counts.append(count)
			i += 1
		i = len(ENTRY_TYPES)
		j = 0
		for aType in ANNOTATION_ANSWER_LINK_TYPES:
			if aType in ANNOTATION_TYPES:
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Annotation.all().filter("creator = ", self.key()).filter("character = ", None).filter("type = ", aType).count()
				counts.append(count)
			elif aType == "answer":
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Answer.all().filter("creator = ", self.key()).filter("character = ", None).count()
				counts.append(count)
			elif aType == "link":
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Link.all().filter("creator = ", self.key()).count()
				counts.append(count)
			i += 1
			j += 1
		return countNames, counts
	
	# DISPLAY
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		if self.isOnlineMember:
			offlineImageString = ""
		else:
			name = TEMPLATE_TERMS["template_offline_member"]
			offlineImageString = '<img src="/images/offline.png" alt="%s" title="%s"> ' % (name, name)
 		return '%s<a href="%s?%s">%s</a>' % (offlineImageString, self.urlWithoutQuery(), self.urlQuery(), self.nickname)
	
	def askLinkString(self):
		return '<a href="%s?%s">%s</a>' % (self.askUrlWithoutQuery(), self.urlQuery(), self.nickname)
	
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_member"])

	def askUrlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_ask"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_member"], self.getKeyName())

	def imageEmbed(self):
		return '<img src="/%s/%s?%s=%s" class="bordered">' % (DIRS["dir_visit"], URLS["url_image"], URL_IDS["url_query_member"], self.getKeyName())
	
# ============================================================================================
# ============================================================================================
class ViewOptions(db.Model): 
# ============================================================================================
# options on what to show - four per member (home, entry, member, character)
# # parent: member; URL lookup: not needed
# ============================================================================================

	member = db.ReferenceProperty(Member, required=True, collection_name="view_options_to_member")
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="view_options_to_rakontu")
	location = db.StringProperty(choices=VIEW_OPTION_LOCATIONS, default="home") 
	
	endTime = TzDateTimeProperty(auto_now_add=True, indexed=False)
	timeFrameInSeconds = db.IntegerProperty(default=WEEK_SECONDS, indexed=False)

	entryTypes = db.ListProperty(bool, default=[True, True, False, False, False], indexed=False) # stories and invitations on by default
	annotationAnswerLinkTypes = db.ListProperty(bool, default=[False, True, True, False, False, False], indexed=False) # "tag set", "comment", "request", "nudge", "answer", "link"
	
	nudgeCategories = db.ListProperty(bool, default=[True] * NUM_NUDGE_CATEGORIES, indexed=False)
	nudgeFloor = db.IntegerProperty(default=DEFAULT_NUDGE_FLOOR, indexed=False)
	
	search = db.ReferenceProperty(None, collection_name="view_options_to_search", indexed=False)
	
	limitPerPage = db.IntegerProperty(default=MAX_ITEMS_PER_GRID_PAGE, indexed=False) # may want to set this later, just constant for now
	
	showDetails = db.BooleanProperty(default=True, indexed=False)
	showOptionsOnTop = db.BooleanProperty(default=False, indexed=False)
	
	def getStartTime(self):
		return self.endTime - timedelta(seconds=self.timeFrameInSeconds)
	
	def getFrameStringForViewTimeFrame(self):
		for aFrame, seconds in TIME_FRAMES:
			if self.timeFrameInSeconds == seconds:
				return aFrame
		return None
	
	def setViewTimeFrameFromTimeFrameString(self, frame):
		for aFrame, seconds in TIME_FRAMES:
			if frame == aFrame:
				self.timeFrameInSeconds = seconds
				self.put()
				break
			
	def displayNameForLocation(self):
		i = 0
		for aLocation in VIEW_OPTION_LOCATIONS:
			if self.location == aLocation:
				return VIEW_OPTION_LOCATIONS_DISPLAY[i]
			i += 1
		return None
			
# ============================================================================================
# ============================================================================================
class PendingMember(db.Model): 
# ============================================================================================
# person invited to join rakontu but not yet logged in
# parent: rakontu; no lookup required
# ============================================================================================

	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="pending_members_to_rakontu")
	email = db.StringProperty(required=True) # must match google account
	invited = TzDateTimeProperty(auto_now_add=True)
	governanceType = db.StringProperty(default="member")
	
	def governanceTypeForDisplay(self):
		# GOVERNANCE_ROLE_TYPES_DISPLAY = ["member", "manager", "owner"]
		if self.governanceType == "member":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[0]
		elif self.governanceType == "manager":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[1]
		elif self.governanceType == "owner":
			return GOVERNANCE_ROLE_TYPES_DISPLAY[2]
	
# ============================================================================================
# ============================================================================================
class Character(db.Model):
# ============================================================================================
# optional fictions to anonymize entries but provide some information about intent
# parent: rakontu; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="characters_to_rakontu")
	name = db.StringProperty(required=True)
	created = TzDateTimeProperty(auto_now_add=True)
	active = db.BooleanProperty(default=True)
	
	description = db.TextProperty(default=None) # appears on rakontu page
	description_formatted = db.TextProperty()
	description_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	etiquetteStatement = db.TextProperty(default=None) # appears under "how to be [name]"
	etiquetteStatement_formatted = db.TextProperty()
	etiquetteStatement_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	image = db.BlobProperty(default=None) # optional
	
	def removeAllDependents(self):
		db.delete(Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER))

	def isMember(self):
		return False
	
	def getAllItemsAttributedToCharacter(self):
		result = []
		result.extend(self.getNonDraftEntriesAttributedToCharacter())
		result.extend(self.getAnnotationsAttributedToCharacter())
		result.extend(self.getAnswersAboutEntriesAttributedToCharacter())
		return result

	def browseItems(self, minTime, maxTime, entryTypes, annotationTypes):
		result = []
		entries = Entry.all().filter("character = ", self.key()).filter("draft = ", False).\
			filter("type IN ", entryTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
		result.extend(entries)
		annotations = Annotation.all().filter("character = ", self.key()).\
			filter("type IN ", annotationTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
		result.extend(annotations)
		if "answer" in annotationTypes:
			answers = Answer.all().filter("character = ", self.key()).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(answers)
		return result
	
	def selectItemsFromList(self, items, minTime, maxTime, entryTypes, annotationTypes):
		result = []
		for item in items:
			if item.published and item.published >= minTime and item.published <= maxTime:
				if item.__class__.__name__ == "Entry":
					if item.type in entryTypes:
						result.append(item)
				elif item.__class__.__name__ == "Annotation":
					if item.type in annotationTypes:
						result.append(item)
				elif item.__class__.__name__ == "Answer":
					if "answer" in annotationTypes:
						result.append(item)
				elif item.__class__.__name__ == "Link":
					if "link" in annotationTypes:
						result.append(item)
		return result
			
	def getCounts(self):
		countNames = []
		counts = []
		i = 0
		for aType in ENTRY_TYPES:
			countNames.append(ENTRY_TYPES_PLURAL_DISPLAY[i])
			count = Entry.all().filter("character = ", self.key()).filter("type = ", aType).count()
			counts.append(count)
			i += 1
		i = len(ENTRY_TYPES)
		j = 0
		for aType in ANNOTATION_ANSWER_LINK_TYPES:
			if aType in ANNOTATION_TYPES:
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Annotation.all().filter("character = ", self.key()).filter("type = ", aType).count()
				counts.append(count)
			elif aType == "answer":
				countNames.append(ANNOTATION_ANSWER_LINK_TYPES_PLURAL_DISPLAY[j])
				count = Answer.all().filter("character = ", self.key()).count()
				counts.append(count)
			elif aType == "link":
				pass  # characters can't do links
			i += 1
			j += 1
		return countNames, counts
		
	def getNonDraftEntriesAttributedToCharacter(self):
		return Entry.all().filter("character = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getAnnotationsAttributedToCharacter(self):
		return Annotation.all().filter("character = ", self.key()).fetch(FETCH_NUMBER)
	
	def getAnswersAboutEntriesAttributedToCharacter(self):
		return Answer.all().filter("character = ", self.key()).filter("referentType = ", "entry").fetch(FETCH_NUMBER)

	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s">%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.name)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_character"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_character"], self.key().name())
	
	def imageEmbed(self):
		return '<img src="/%s/%s?%s=%s">' % (DIRS["dir_visit"], URLS["url_image"], URL_IDS["url_query_character"], self.getKeyName())
		
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
	
	def getAnswerForQuestion(self, question):
		return Answer.all().filter("referent = ", self.key()).filter("question = ", question.key()).get()
		
# ============================================================================================
# ============================================================================================
class SavedSearch(db.Model): 
# ============================================================================================
# search parameters, also called search filter or just filter
# parent: member; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="searches_to_rakontu")
	creator = db.ReferenceProperty(Member, required=True, collection_name="searches_to_member")
	private = db.BooleanProperty(default=True)
	created = TzDateTimeProperty(auto_now_add=True)
	name = db.StringProperty(default=DEFAULT_SEARCH_NAME)
	# the type is mainly to make it display in a list of entries, but it may be useful later anyway
	type = db.StringProperty(default="search filter", indexed=False) 
	
	flaggedForRemoval = db.BooleanProperty(default=False)
	flagComment = db.StringProperty(indexed=False)

	words_anyOrAll = db.StringProperty(choices=ANY_ALL, default="any", indexed=False)
	words_locations = db.ListProperty(bool, default=[True] * (len(ANNOTATION_TYPES) + 1), indexed=False)
	words = db.StringListProperty(indexed=False)
	
	tags_anyOrAll = db.StringProperty(choices=ANY_ALL, indexed=False)
	tags = db.StringListProperty(indexed=False)
	
	overall_anyOrAll = db.StringProperty(choices=ANY_ALL, default="any", indexed=False)
	answers_anyOrAll = db.StringProperty(choices=ANY_ALL, default="any", indexed=False)
	creatorAnswers_anyOrAll = db.StringProperty(choices=ANY_ALL, default="any", indexed=False)
	
	comment = db.TextProperty(default="")
	comment_formatted = db.TextProperty()
	comment_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)

	def copyDataFromOtherSearchAndPut(self, search, refs):
		self.private = True
		self.name = "%s %s" % (TERMS["term_copy_of"], search.name)
		self.words_anyOrAll = search.words_anyOrAll
		self.words_locations = []
		self.words_locations.extend(search.words_locations)
		self.words = []
		self.words.extend(search.words)
		self.tags_anyOrAll = search.tags_anyOrAll
		self.tags = []
		self.tags.extend(search.tags)
		self.answers_anyOrAll = search.answers_anyOrAll
		self.creatorAnswers_anyOrAll = search.creatorAnswers_anyOrAll
		self.comment = db.Text(search.comment)
		self.comment_formatted = db.Text(search.comment_formatted)
		self.comment_format = search.comment_format
		thingsToPut = []
		for ref in refs:
			keyName = GenerateSequentialKeyName("searchref")
			myRef = SavedSearchQuestionReference(
												key_name=keyName,
												parent=self,
												rakontu=self.rakontu, 
												creator=self.creator,
												search=self, 
												questionName=ref.questionName,
												questionType=ref.questionType,
												type=ref.type,
												order=ref.order,
												answer=ref.answer,
												comparison=ref.comparison
												)
			thingsToPut.append(myRef)
		db.put(thingsToPut)
	
	def getQuestionReferences(self):
		return SavedSearchQuestionReference.all().filter("search = ", self.key()).fetch(FETCH_NUMBER)
	
	def getQuestionReferencesOfType(self, type):
		return SavedSearchQuestionReference.all().filter("search = ", self.key()).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def getQuestionReferenceForQuestionNameTypeAndOrder(self, name, type, order):
		return SavedSearchQuestionReference.all().filter("search = ", self.key()).\
			filter("questionName = ", name).\
			filter("questionType = ", type).\
			filter("order = ", order).get()
	
	def getEntryQuestionRefs(self):
		return self.getQuestionReferencesOfType("entry")
	
	def getCreatorQuestionRefs(self):
		return self.getQuestionReferencesOfType("creator")
	
	def getIncomingLinks(self):
		return Link.all().filter("itemTo = ", self.key()).fetch(FETCH_NUMBER)
	
	def removeAllDependents(self):
		db.delete(self.getQuestionReferences())
			
	def notPrivate(self):
		return self.private == False
	
	def displayString(self):
		if self.private:
			return self.name
		else:
			return "%s (%s)" % (self.name, self.creator.linkString())
	
	# LINKING TO PATTERNS
		
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s">%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.name)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def editURL(self):
		return "/%s/%s?%s" % (DIRS["dir_visit"], URLS["url_search_filter"], self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_home"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_search_filter"], self.key().name())

	def description(self):
		result = ""
		if self.words:
			result += '<p>%s %s "%s"</p>' % (self.words_anyOrAll, TERMS["term_of_the_words"], ",".join(self.words))
		if self.tags:
			result += '<p>%s %s "%s"</p>' % (self.tags_anyOrAll, TERMS["term_of_the_tags"], ",".join(self.tags))
		entryRefs = self.getEntryQuestionRefs()
		if entryRefs:
			result += "<p>%s %s " % (self.answers_anyOrAll, TERMS["term_of_the_entry_questions"])
			for ref in entryRefs:
				result += '%s %s ' % (ref.question.text, ref.answer)
			result += "</p>"
		creatorRefs = self.getCreatorQuestionRefs()
		if creatorRefs:
			result += "<p>%s %s " % (self.creatorAnswers_anyOrAll, TERMS["term_of_the_creator_questions"])
			for ref in creatorRefs:
				result += ' %s %s ' % (ref.question.text, ref.answer)
			result += "</p>"
		return result
	
	def isEntry(self):
		# has to do with linking to patterns
		return False 
	
# ============================================================================================
# ============================================================================================
class SavedSearchQuestionReference(db.Model): 
# ============================================================================================
# reference to the use of a question in the search filter
# parent: savedsearch; URL lookup: none needed
# ============================================================================================

	created = TzDateTimeProperty(auto_now_add=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="searchrefs_to_rakontu")
	search = db.ReferenceProperty(SavedSearch, required=True, collection_name="question_refs_to_saved_search")
	
	questionName = db.StringProperty(required=True)
	questionType = db.StringProperty(required=True)
	
	type = db.StringProperty() # entry or creator
	order = db.IntegerProperty()
	answer = db.StringProperty(indexed=False)
	comparison = db.StringProperty(indexed=False)
	
	def matchesQuestionInfo(self, name, type, order, answer=None):
		if answer:
			return self.questionName == name and self.questionType == type and self.order == order and self.answer == answer
		else:
			return self.questionName == name and self.questionType == type and self.order == order
	
	def matchesComparisonAndOrder(self, comparison, order):
		return self.comparison == comparison and self.order == order
	
# ============================================================================================
# ============================================================================================
class Answer(db.Model): 
# ============================================================================================
# answer to a question (about entry, character or member)
# parent: member, character or entry; URL lookup: none needed, never looked up directly
# ============================================================================================

	rakontu = db.ReferenceProperty(Rakontu, collection_name="answers_to_rakontu")
	question = db.ReferenceProperty(Question, collection_name="answers_to_questions")
	referent = db.ReferenceProperty(None, collection_name="answers_to_objects") # entry or member
	referentType = db.StringProperty(default="entry") # entry or member
	creator = db.ReferenceProperty(Member, collection_name="answers_to_creators") 
	
	collectedOffline = db.BooleanProperty(default=False, indexed=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="answers_to_liaisons")
	character = db.ReferenceProperty(Character, default=None, collection_name="answers_to_characters")
	
	inBatchEntryBuffer = db.BooleanProperty(default=False) # in the process of being imported, not "live" yet
	flaggedForRemoval = db.BooleanProperty(default=False)
	flagComment = db.StringProperty(indexed=False)
	
	answerIfBoolean = db.BooleanProperty(default=False, indexed=False)
	answerIfText = db.StringProperty(default="", indexed=False)
	answerIfMultiple = db.StringListProperty(default=[""] * MAX_NUM_CHOICES_PER_QUESTION, indexed=False)
	answerIfValue = db.IntegerProperty(default=0, indexed=False)
	
	collected = TzDateTimeProperty(default=None, indexed=False)
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True, indexed=False)
	published = TzDateTimeProperty(auto_now_add=True)
	
	entryNudgePointsWhenPublished = db.ListProperty(int, default=[0] * NUM_NUDGE_CATEGORIES, indexed=False)
	entryActivityPointsWhenPublished = db.IntegerProperty(default=0, indexed=False)
	
	def isAnswer(self):
		return True
	
	def getClassName(self):
		return self.__class__.__name__
	
	# IMPORTANT METHODS
	
	def setValueBasedOnResponse(self, question, request, queryText, response):
		if question.type == "text":
			self.answerIfText = htmlEscape(response)
		elif question.type == "value":
			oldValue = self.answerIfValue
			try:
				self.answerIfValue = int(response)
			except:
				self.answerIfValue = oldValue
		elif question.type == "boolean":
			self.answerIfBoolean = response == "yes"
		elif (question.type == "nominal" or question.type == "ordinal"):
			if question.multiple:
				self.answerIfMultiple = []
				for choice in question.choices:
					if request.get("%s|%s" % (queryText, choice)) == "yes":
						self.answerIfMultiple.append(choice)
			else:
				self.answerIfText = response
	
	def publish(self):
		if self.referentType == "entry":
			self.published = datetime.now(pytz.utc)
			self.referent.recordAction("added", self, "Answer")
			for i in range(NUM_NUDGE_CATEGORIES):
				if self.rakontu.nudgeCategoryIndexHasContent(i):
					self.entryNudgePointsWhenPublished[i] = self.referent.nudgePoints[i]
			self.entryActivityPointsWhenPublished = self.referent.activityPoints
			self.creator.nudgePoints += self.rakontu.getMemberNudgePointsForEvent("answering question")
		# caller must do puts
		
	# DISPLAY
		
	def getImageLinkForType(self):
		return ImageLinkForAnswer(-1) # -1 means don't put a count tooltip
	
	def displayStringShort(self):
		return self.displayString(includeQuestionText=False, includeQuestionName=False)
	
	def displayString(self, includeQuestionText=True, includeQuestionName=False):
		result = ""
		if includeQuestionText:
			result += self.question.text + " "
		if includeQuestionName:
			result += self.question.name + ": "
		if self.question.type == "boolean":
			if self.answerIfBoolean: 
				result += TERMS["term_yes"]
			else:
				result += TERMS["term_no"]
		elif self.question.type == "text":
			result += self.answerIfText
		elif self.question.type == "ordinal" or self.question.type == "nominal":
			if self.question.multiple:
				answersToReport = []
				for answer in self.answerIfMultiple:
					if len(answer):
						answersToReport.append(answer)
				result +=  ", ".join(answersToReport)
			else:
				result +=  self.answerIfText
		elif self.question.type == "value":
			result +=  "%s" % self.answerIfValue
		return result
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return self.displayString()
	
	def linkStringWithQuestionName(self):
		return self.displayString(includeQuestionName=True, includeQuestionText=False)
	
	def linkStringWithQuestionText(self):
		return self.displayString(includeQuestionName=False, includeQuestionText=True, )
	
	def linkStringWithQuestionNameAndReferentLink(self):
		try:
			return "%s for %s" % (self.linkStringWithQuestionName(), self.referent.linkString())
		except:
			return self.linkStringWithQuestionName()
		
	def linkStringWithQuestionTextAndReferentLink(self):
		try:
			return "%s for %s" % (self.linkStringWithQuestionText(), self.referent.linkString())
		except:
			return self.linkStringWithQuestionText()
	
	def PrintText(self, member):
		answerString = TERMS["term_answer"].capitalize()
		name = self.memberNickNameOrCharacterName()
		time = TimeDisplay(self.published, member)
		text = self.displayStringShort()
		return '<p><b>%s</b>: %s [%s, %s]<div style="padding: 0px 16px 0px 16px;">%s</div></p><hr>\n\n' % \
			(answerString, self.question.text, name, time, text)
			
	def MemberWantsToSeeMyTypeInLocation(self, member, location):
		return member.getAnnotationAnswerLinkTypeForLocationAndIndex(location, ANNOTATION_ANSWER_LINK_TYPES_ANSWER_INDEX)
			
	def getEntryNudgePointsWhenPublishedForExistAndShowOptions(self, exist, show):
		result = 0
		for i in range(NUM_NUDGE_CATEGORIES):
			if exist[i] and show[i]:
				result += self.entryNudgePointsWhenPublished[i]
		return result
	
	# ATTRIBUTION
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else:
			return self.creator.nickname
		
	def questionKey(self):
		return self.question.key()
	

# ============================================================================================
# ============================================================================================
class Entry(db.Model):
# ============================================================================================
# main element of data: story, invitation, collage, pattern, resource
# parent: member; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	type = db.StringProperty(choices=ENTRY_TYPES, required=True) 
	title = db.StringProperty(required=True, default=DEFAULT_UNTITLED_ENTRY_TITLE)
	text = db.TextProperty(default=NO_TEXT_IN_ENTRY)
	text_formatted = db.TextProperty()
	text_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	resourceForHelpPage = db.BooleanProperty(default=False)
	resourceForNewMemberPage = db.BooleanProperty(default=False)
	resourceForManagersAndOwnersOnly = db.BooleanProperty(default=False)
	categoryIfResource = db.StringProperty(default="")
	orderIfResource = db.IntegerProperty(default=0)
	
	rakontu = db.ReferenceProperty(Rakontu, collection_name="entries_to_rakontu")
	creator = db.ReferenceProperty(Member, collection_name="entries_to_members")
	collectedOffline = db.BooleanProperty(default=False, indexed=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="entries_to_liaisons")
	character = db.ReferenceProperty(Character, default=None, collection_name="entries_to_characters")
	
	additionalEditors = db.StringListProperty() # curators, guides, liaisons, managers, members, list
	
	draft = db.BooleanProperty(default=True)
	inBatchEntryBuffer = db.BooleanProperty(default=False) # in the process of being imported, not "live" yet
	flaggedForRemoval = db.BooleanProperty(default=False)
	flagComment = db.StringProperty(indexed=False)
	
	collected = TzDateTimeProperty(default=None, indexed=False)
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True, indexed=False)
	published = TzDateTimeProperty(auto_now_add=True)
	
	lastRead = TzDateTimeProperty(default=None)
	lastAnnotatedOrAnsweredOrLinked = TzDateTimeProperty(default=None)
	activityPoints = db.IntegerProperty(default=0)
	nudgePoints = db.ListProperty(int, default=[0] * NUM_NUDGE_CATEGORIES)
	numAnnotations = db.ListProperty(int, default=[0] * len(ANNOTATION_TYPES), indexed=False)
	numAnswers = db.IntegerProperty(default=0, indexed=False)
	numLinks = db.IntegerProperty(default=0, indexed=False)
	
	def isEntry(self):
		return True
	
	def collectedOfflineOrInBatchEntryBuffer(self):
		return self.collectedOffline or self.inBatchEntryBuffer
	
	def getClassName(self):
		return self.__class__.__name__
	
	def isForEveryoneIfResource(self):
		return not self.resourceForManagersAndOwnersOnly
	
	def getAdditionalEditorTypes(self):
		result = []
		for editorTypeOrKey in self.additionalEditors:
			found = False
			for possibleType in ADDITIONAL_EDITOR_TYPES:
				if editorTypeOrKey == possibleType:
					found = True
					break
			if found:
				result.append(possibleType)
		return result
		
	def getAdditionalEditorKeys(self):
		result = []
		for editorTypeOrKey in self.additionalEditors:
			found = False
			for possibleType in ADDITIONAL_EDITOR_TYPES:
				if editorTypeOrKey == possibleType:
					found = True
					break
			if not found:
				result.append(editorTypeOrKey)
		return result
	
	def memberCanEditMe(self, member):
		if str(member.key()) == str(self.creator.key()):
			return True
		for editorTypeOrKey in self.additionalEditors:
			if editorTypeOrKey == "curators":
				if member.isCurator():
					return True
			elif editorTypeOrKey == "guides":
				if member.isGuide():
					return True
			elif editorTypeOrKey == "liaisons":
				if member.isLiaison():
					return True
			elif editorTypeOrKey == "managers":
				if member.isManagerOrOwner():
					return True
			elif editorTypeOrKey == "members":
				return True
			elif editorTypeOrKey == str(member.key()):
				return True
		return False
		
		
	# IMPORTANT METHODS
	
	def publish(self, isFirstPublish=True):
		self.draft = False
		self.published = datetime.now(pytz.utc)
		# entries, unlike other things, can be published multiple times.
		# however, they should only update the creator's nudge points once
		# (espcially since later publishers may be others, if the creator has added additional editors)
		# the activity points WILL go up on additional publishing, however, which makes sense.
		self.recordAction("added", self, "Entry")
		if isFirstPublish:
			self.creator.nudgePoints += self.rakontu.getMemberNudgePointsForEvent("adding %s" % self.type)
		# caller must do puts
					
	def unPublish(self):
		if not self.character:
			self.creator.decrementCount(self.type)
		# caller must do puts
		
	def recordAction(self, action, referent, className):
		now = datetime.now(pytz.utc)
		if className == "Entry":
			if action == "read":
				eventType = "reading"
				self.lastRead = now
			elif action =="added":
				eventType = "adding %s" % self.type
		elif className == "Annotation":
			if action == "read":
				eventType = "reading"
				self.lastRead = now # reading an annotation counts as reading the entry
			else:
				eventType = "adding %s" % referent.type
			self.lastAnnotatedOrAnsweredOrLinked = now
			typeIndex = -1
			i = 0
			for type in ANNOTATION_TYPES:
				if type == referent.type:
					typeIndex = i
					break
				i += 1
			if typeIndex >= 0:
				self.numAnnotations[typeIndex] = self.numAnnotations[typeIndex] + 1
			if referent.type == "nudge":
				self.updateNudgePointsIncludingUnsavedOne(referent)
		elif className == "Answer":
			eventType = "answering question"
			self.lastAnnotatedOrAnsweredOrLinked = now
			self.numAnswers += 1
		elif className == "Link":
			eventType = "adding %s link" % referent.type 
			self.lastAnnotatedOrAnsweredOrLinked = now
			self.numLinks += 1
		self.activityPoints += self.rakontu.getEntryActivityPointsForEvent(eventType)
		# caller must do puts
		
	def updateNudgePointsIncludingUnsavedOne(self, nudge):
		self.nudgePoints = [0] * NUM_NUDGE_CATEGORIES
		annotations = Annotation.all().ancestor(self)
		for i in range(NUM_NUDGE_CATEGORIES):
			for annotation in annotations:
				if annotation.type == "nudge":
					self.nudgePoints[i] += annotation.valuesIfNudge[i]
			if nudge:
				self.nudgePoints[i] += nudge.valuesIfNudge[i]
		# caller must do put
		
	def updateAnnotationAnswerLinkCounts(self):
		for i in range(len(ANNOTATION_TYPES)):
			self.numAnnotations[i] = self.numAnnotationsOfType(ANNOTATION_TYPES[i])
		self.numAnswers = Answer.all().ancestor(self).count()
		self.numLinks = self.getNumLinks()
		# this counts as a reading for the purpose of time checking, but does not add to the activity points
		self.lastRead = datetime.now(tz=pytz.utc) 
		self.put()
		
	def addCurrentTextToPreviousVersions(self):
		keyName = GenerateSequentialKeyName("version")
		version = TextVersion(
							key_name=keyName, 
							parent=self,
							id=keyName,
							entry=self.key(), 
							rakontu=self.rakontu.key(),
							title=self.title,
							text=self.text,
							text_format=self.text_format,
							text_formatted=self.text_formatted,
							)
		version.put()
		
	def getTextVersions(self):
		return TextVersion.all().filter("entry = ", self.key()).fetch(FETCH_NUMBER)
	
	def getTextVersionsInTimeOrder(self):
		return TextVersion.all().filter("entry = ", self.key()).order("created").fetch(FETCH_NUMBER)
	
	def getTextVersionsInReverseTimeOrder(self):
		return TextVersion.all().filter("entry = ", self.key()).order("-created").fetch(FETCH_NUMBER)
	
	def lastTouched(self):
		if self.lastRead and self.lastAnnotatedOrAnsweredOrLinked and self.published:
			return max(self.lastRead, max(self.lastAnnotatedOrAnsweredOrLinked, self.published))
		elif self.lastRead and self.published:
			return max(self.lastRead, self.published)
		elif self.lastAnnotatedOrAnsweredOrLinked and self.published:
			return max(self.lastAnnotatedOrAnsweredOrLinked, self.published)
		elif self.published:
			return self.published
		else:
			return None
		
	def lastPublishedOrAnnotated(self):
		if self.lastAnnotatedOrAnsweredOrLinked:
			return self.lastAnnotatedOrAnsweredOrLinked
		else:
			return self.published
		
	def removeAllDependents(self):
		db.delete(self.getAttachments())
		db.delete(self.getAllLinks())
		db.delete(self.getAnswers())
		db.delete(self.getAnnotations())
		db.delete(self.getTextVersions())
		
	def listAllDependents(self):
		result = []
		result.extend(self.getAttachments())
		result.extend(self.getAllLinks())
		result.extend(self.getAnswers())
		result.extend(self.getAnnotations())
		result.extend(self.getTextVersions())
		return result
		
	def satisfiesSearchCriteria(self, search, entryRefs, creatorRefs):
		if not search.words and not search.tags and not entryRefs and not creatorRefs: # empty search
			return True
		if search.overall_anyOrAll == "any":
			satisfiesWords = False
			satisfiesTags = False
			satisfiesEntryQuestions = False
			satisfiesCreatorQuestions = False
		else:
			satisfiesWords = True
			satisfiesTags = True
			satisfiesEntryQuestions = True
			satisfiesCreatorQuestions = True
		if search.words:
			satisfiesWords = self.satisfiesWordSearch(search.words_anyOrAll, search.words_locations, search.words)
		if search.tags:
			satisfiesTags = self.satisfiesTagSearch(search.tags_anyOrAll, search.tags)
		if entryRefs:
			satisfiesEntryQuestions = self.satisfiesQuestionSearch(search.answers_anyOrAll, entryRefs, False)
		if creatorRefs:
			satisfiesCreatorQuestions = self.satisfiesQuestionSearch(search.creatorAnswers_anyOrAll, creatorRefs, True)
		if search.overall_anyOrAll == "any":
			return satisfiesWords or satisfiesTags or satisfiesEntryQuestions or satisfiesCreatorQuestions
		else:
			return satisfiesWords and satisfiesTags and satisfiesEntryQuestions and satisfiesCreatorQuestions
		
	def satisfiesQuestionSearch(self, anyOrAll, refs, aboutCreator):
		numAnswerSearchesSatisfied = 0
		for ref in refs:
			match = False
			if aboutCreator:
				try: # in case creator doesn't exist
					if self.character:
						answers = self.character.getAnswers()
					else:
						if self.creator.active:
							answers = self.creator.getAnswers()
						else:
							return False
				except:
					return False
			else:
				answers = self.getAnswers()
			matchingAnswers = []
			for answer in answers:
				if answer.question.name == ref.questionName and answer.question.type == ref.questionType:
					matchingAnswers.append(answer)
			if matchingAnswers:
				for answer in matchingAnswers:
					if ref.questionType == "text":
						if ref.comparison == "contains":
							match = caseInsensitiveFind(answer.answerIfText, ref.answer)
						elif ref.comparison == "is":
							match = answer.answerIfText.lower() == ref.answer.lower()
					elif ref.questionType == "value":
						if ref.comparison == "is less than":
							try:
								answerValue = int(ref.answer)
								match = answer.answerIfValue < answerValue
							except:
								match = False
						elif ref.comparison == "is greater than":
							try:
								answerValue = int(ref.answer)
								match = answer.answerIfValue > answerValue
							except:
								match = False
						elif ref.comparison == "is":
							try:
								answerValue = int(ref.answer)
								match = answer.answerIfValue == answerValue
							except:
								match = False
					elif ref.questionType == "ordinal" or ref.questionType == "nominal":
						# ignore whether it is multiple choice or not - if it has it, it has it
						foundChoice = False
						for choice in answer.answerIfMultiple:
							if ref.answer == choice:
								foundChoice = True
								break
						match = foundChoice or ref.answer == answer.answerIfText
					elif ref.questionType == "boolean":
						if ref.answer == "yes":
							match = answer.answerIfBoolean == True
						else:
							match = answer.answerIfBoolean == False
					if match:
						break # don't need to check if more than one answer matches
			if match:
				numAnswerSearchesSatisfied += 1
		if anyOrAll == "any":
			return numAnswerSearchesSatisfied > 0
		else:
			return numAnswerSearchesSatisfied >= len(refs)
	
	def satisfiesWordSearch(self, anyOrAll, locations, words):
		numWordSearchesSatisfied = 0
		for word in words:
			match = False
			if locations[0]: #"in the title"
				match = match or caseInsensitiveFind(self.title, word) 
			if locations[1]: #"in the text"
				match = match or caseInsensitiveFind(self.text, word) 
			if locations[2]: #"in a comment"
				match = match or self.wordIsFoundInAComment(word)
			if locations[3]: #"in a request"
				match = match or self.wordIsFoundInARequest(word)
			if locations[4]: #"in a nudge comment"
				match = match or self.wordIsFoundInANudgeComment(word)
			if locations[5]: #"in a link comment"
				match = match or self.wordIsFoundInALinkComment(word)
			if match:
				numWordSearchesSatisfied += 1
		if anyOrAll == "any":
			return numWordSearchesSatisfied > 0
		else:
			return numWordSearchesSatisfied >= len(words)

	def wordIsFoundInAComment(self, word):
		comments = self.getAnnotationsOfType("comment")
		for comment in comments:
			if caseInsensitiveFind(comment.longString, word):
				return True
		return False
	
	def wordIsFoundInARequest(self, word):
		requests = self.getAnnotationsOfType("request")
		for request in requests:
			if caseInsensitiveFind(request.longString, word):
				return True
		return False
	
	def wordIsFoundInANudgeComment(self, word):
		nudges = self.getAnnotationsOfType("nudge")
		for nudge in nudges:
			if caseInsensitiveFind(nudge.shortString, word):
				return True
		return False
	
	def wordIsFoundInALinkComment(self, word):
		links = self.getAllLinks()
		for link in links:
			if caseInsensitiveFind(link.comment, word):
				return True
		return False
	
	def satisfiesTagSearch(self, anyOrAll, words):
		numWordSearchesSatisfied = 0
		for word in words:
			match = False
			tagsets = self.getAnnotationsOfType("tag set")
			for tagset in tagsets:
				for tag in tagset.tagsIfTagSet:
					match = match or caseInsensitiveFind(tag, word)
			if match:
				numWordSearchesSatisfied += 1
		if anyOrAll == "any":
			return numWordSearchesSatisfied > 0
		else:
			return numWordSearchesSatisfied >= len(words)

	def satisfiesEntryTypesCriteria(self, entryTypesToInclude):
		i = 0
		for type in ENTRY_TYPES:
			if type == self.type:
				if not entryTypesToInclude[i]:
					return False
			i += 1
		return True
	
	# TYPE
	
	def isStory(self):
		return self.type == "story"
	
	def isInvitation(self):
		return self.type == "invitation"
	
	def isCollage(self):
		return self.type == "collage"
	
	def isPattern(self):
		return self.type == "pattern"
	
	def isResource(self):
		return self.type == "resource"
	
	def isPatternOrCollage(self):
		return self.type == "pattern" or self.type == "collage"
	
	def isCollageOrResource(self):
		return self.type == "collage" or self.type == "resource"
	
	# MEMBERS
		
	def getPublishDateForMember(self, member):
		if member:
			localTime = self.published.astimezone(timezone(member.timeZoneName))
			return localTime.strftime(str(member.timeFormat))
		else:
			return self.published
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else: 
			return self.creator.nickname
		
	# NUDGE SYSTEM

	def getNudgesForMember(self, member):
		return Annotation.all().filter("entry = ", self.key()).filter("type = ", "nudge").filter("creator = ", member.key()).fetch(FETCH_NUMBER)
	
	def getTotalNudgePointsForMember(self, member):
		nudges = self.getNudgesForMember(member)
		result = 0
		for nudge in nudges:
			result += nudge.totalNudgePointsAbsolute()
		return result
	
	def memberCanNudge(self, member):
		return member.key() != self.creator.key()

	def nudgePointsCombined(self):
		result = 0
		for i in range(NUM_NUDGE_CATEGORIES):
			if self.rakontu.nudgeCategoryIndexHasContent(i):
				result += self.nudgePoints[i]
		return result
	
	def nudgePointsForExistAndShowOptions(self, exist, show):
		result = 0
		for i in range(NUM_NUDGE_CATEGORIES):
			if exist[i] and show[i]:
				result += self.nudgePoints[i]
		return result
	
	# ANNOTATIONS, ANSWERS, LINKS
	
	def getAnnotationsAnswersAndLinks(self):
		result = []
		result.extend(self.getAnnotations())
		result.extend(self.getAnswers())
		result.extend(self.getAllLinks())
		return result
	
	def browseItems(self, minTime, maxTime, annotationTypes):
		result = []
		annotations = Annotation.all().filter("entry = ", self.key()).filter("type IN ", annotationTypes).\
			filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
		result.extend(annotations)
		if "answer" in annotationTypes:
			answers = Answer.all().filter("referent = ", self.key()).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(answers)
		if "link" in annotationTypes:
			linksTo = Link.all().filter("itemTo = ", self.key()).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(linksTo)
			linksFrom = Link.all().filter("itemFrom = ", self.key()).\
				filter("published >= ", minTime).filter("published < ", maxTime).fetch(FETCH_NUMBER)
			result.extend(linksFrom)
		return result
	
	def selectItemsFromList(self, items, annotationTypes):
		result = []
		for item in items:
			if item.__class__.__name__ == "Annotation":
				if item.type in annotationTypes:
					result.append(item)
			elif item.__class__.__name__ == "Answer":
				if "answer" in annotationTypes:
					result.append(item)
			elif item.__class__.__name__ == "Link":
				if "link" in annotationTypes:
					result.append(item)
		return result
	
	def getAnnotations(self):
		return Annotation.all().filter("entry =", self.key()).fetch(FETCH_NUMBER)
	
	def getAnnotations(self):
		return Annotation.all().filter("entry =", self.key()).fetch(FETCH_NUMBER)
	
	def getAnnotationCount(self):
		return Annotation.all().filter("entry =", self.key()).count()
	
	def getAnnotationsOfType(self, type):
		return Annotation.all().filter("entry =", self.key()).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def numAnnotationsOfType(self, type):
		return Annotation.all().filter("entry =", self.key()).filter("type = ", type).count()
	
	def hasTagSets(self):
		return Annotation.all().filter("entry =", self.key()).filter("type = ", "tag set").count() > 0
		
	def hasComments(self):
		return Annotation.all().filter("entry =", self.key()).filter("type = ", "comment").count() > 0
		
	def getComments(self):
		return Annotation.all().filter("entry =", self.key()).filter("type = ", "comment").fetch(FETCH_NUMBER)
		
	def getAttachments(self):
		return Attachment.all().filter("entry =", self.key()).fetch(FETCH_NUMBER)
	
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
	
	def hasAnswers(self):
		return Answer.all().filter("referent = ", self.key()).count() > 0
	
	def getAnswersForQuestion(self, question):
		return Answer.all().filter("referent = ", self.key()).filter("question = ", question.key()).fetch(FETCH_NUMBER)
	
	def getAnswerForQuestionAndMember(self, question, member):
		return Answer.all().filter("question = ", question.key()).filter("referent =", self.key()).filter("creator = ", member.key()).get()
	
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)

	def getAnswersForMember(self, member):
		return Answer.all().filter("referent = ", self.key()).filter("creator = ", member.key()).fetch(FETCH_NUMBER)
	
	def getMembersAndCharactersWhoHaveAnsweredQuestionsAboutMe(self):
		members = []
		characters = []
		answers = Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
		for answer in answers:
			if answer.creator and answer.creator.active:
				if answer.creator.isMember():
					# have to do this silly thing because it won't do an equality test on objects, only on keys
				 	foundIt = False
				 	for member in members:
				 		if answer.creator.key() == member.key():
				 			foundIt = True
				 			break
				 	if not foundIt:
				 		members.append(answer.creator)
				else:
				 	foundIt = False
				 	for character in characters:
				 		if answer.creator.key() == character.key():
				 			foundIt = True
				 			break
				 	if not foundIt:
				 		characters.append(answer.creator)
		return (members, characters)
	
	def getAnswersForCharacter(self, character):
		return Answer.all().filter("referent = ", self.key()).filter("creator = ", character.key()).fetch(FETCH_NUMBER)
	
	def hasAnswersForCharacter(self, character):
		return Answer.all().filter("referent = ", self.key()).filter("creator = ", character.key()).count()
	
	def getAnswerForMemberAndQuestion(self, member, question):
		return Answer.all().filter("referent = ", self.key()).filter("creator = ", member.key()).filter("question = ", question.key()).get()
	
	def getAnswerForCharacterAndQuestion(self, character, question):
		return Answer.all().filter("referent = ", self.key()).filter("character = ", character.key()).filter("question = ", question.key()).get()
	
	def getAllLinks(self):
		result = []
		outgoingLinks = Link.all().filter("itemFrom = ", self.key()).fetch(FETCH_NUMBER)
		incomingLinks = Link.all().filter("itemTo = ", self.key()).fetch(FETCH_NUMBER)
		result.extend(outgoingLinks)
		result.extend(incomingLinks)
		return result
	
	def hasLinks(self):
		return Link.all().filter("itemFrom = ", self.key()).count() + Link.all().filter("itemTo = ", self.key()).count() > 0
	
	def getNumLinks(self):
		return Link.all().filter("itemFrom = ", self.key()).count() + Link.all().filter("itemTo = ", self.key()).count() 
	
	def getLinksOfType(self, type):
		result = []
		outgoingLinks = self.getOutgoingLinksOfType(type)
		incomingLinks = self.getIncomingLinksOfType(type)
		result.extend(outgoingLinks)
		result.extend(incomingLinks)
		return result
	
	def getOutgoingLinksOfType(self, type):
		return Link.all().filter("itemFrom = ", self.key()).filter("type = ", type).filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
	
	def hasOutgoingLinksOfType(self, type):
		return Link.all().filter("itemFrom = ", self.key()).filter("type = ", type).filter("inBatchEntryBuffer = ", False).count() > 0
	
	def getResponses(self):
		result = []
		links = Link.all().filter("itemFrom = ", self.key()).filter("type = ", "responded").filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
		for link in links:
			result.append(link.itemTo)
		return result
	
	def getIncomingLinksOfType(self, type):
		return Link.all().filter("itemTo = ", self.key()).filter("type = ", type).filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
	
	def getOutgoingLinks(self):
		return Link.all().filter("itemFrom = ", self.key()).filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
	
	def getIncomingLinks(self):
		return Link.all().filter("itemTo = ", self.key()).filter("inBatchEntryBuffer = ", False).fetch(FETCH_NUMBER)
	
	def getIncomingLinksOfTypeFromType(self, type, fromType):
		result = []
		incomingLinks = self.getIncomingLinksOfType(type)
		for link in incomingLinks:
			if link.itemFrom.type == fromType:
				result.append(link)
		return result
	
	def copyCollectedDateToAllAnswersAndAnnotations(self):
		annotations = self.getAnnotations()
		for annotation in annotations:
			annotation.collected = self.collected
			annotation.put()
		answers = self.getAnswers()
		for answer in answers:
			answer.collected = self.collected
			answer.put()
				
	# DISPLAY
	
	def displayString(self):
		return self.title
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s" %s>%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.getTooltipText(), self.title)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_read"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_entry"], self.getKeyName())

	def typeAsURL(self):
		return URLForEntryType(self.type)
	
	def typeForDisplay(self):
		return DisplayTypeForEntryType(self.type)
	
	def getTooltipText(self):
		if self.text_formatted:
			return'title="%s (%s)"' % (stripTags(self.text_formatted[:TOOLTIP_LENGTH]), self.memberNickNameOrCharacterName())
		else:
			return ""
	
	def getImageLinkForType(self):
		text = self.getTooltipText()
		if self.type == "story":
			name = TEMPLATE_TERMS["template_story"]
			imageText = '<img src="/images/story.png" alt="%s" title="%s" border="0" %s\>' % (name, name, text)
		elif self.type == "pattern":
			name = TEMPLATE_TERMS["template_pattern"]
			imageText = '<img src="/images/pattern.png" alt="%s" title="%s" border="0" %s\>' % (name, name, text)
		elif self.type == "collage":
			name = TEMPLATE_TERMS["template_collage"]
			imageText = '<img src="/images/collage.png" alt="%s" title="%s" border="0" %s\>' % (name, name, text)
		elif self.type == "invitation":
			name = TEMPLATE_TERMS["template_invitation"]
			imageText = '<img src="/images/invitation.png" alt="%s" title="%s" border="0" %s\>' % (name, name, text)
		elif self.type == "resource":
			name = TEMPLATE_TERMS["template_resource"]
			imageText = '<img src="/images/resource.png" alt="%s" title="%s" border="0" %s\>' % (name, name, text)
		return imageText
	
	def displayTextWithInlineAttachmentLinks(self):
		result = self.text_formatted
		attachments = self.getAttachments()
		for i in range(len(attachments)):
			findString = "#%s#" % (i+1)
			if result.find(findString) >= 0:
				if attachments[i].isImage():
					result = result.replace(findString, '<img src="/img?attachment_id=%s">' % attachments[i].key())
				else:
					result = result.replace(findString, '<a href="/visit/attachment?attachment_id=%s">%s</a>' % (attachments[i].key(), attachments[i].fileName))
		return result
	
	def titleWithCategoryIfResource(self):
		if self.type == "resource" and self.categoryIfResource:
			return "%s: %s" % (self.categoryIfResource, self.title)
		else:
			return self.title
	
	# EXPORT
	
	def csvLineWithAnswers(self, member, questions, memberQuestions, characterQuestions):
		timeString = TimeDisplay(self.published, member)
		if self.text_formatted:
			text = self.text_formatted
		else:
			text = ""
		parts = [self.title, timeString, text, self.memberNickNameOrCharacterName()]
		(members, characters) = self.getMembersAndCharactersWhoHaveAnsweredQuestionsAboutMe()
		for aMember in members:
			parts.append("\n%s" % self.title)
			parts.append(timeString)
			parts.append(text)
			parts.append(aMember.nickname)
			# questions about entry
			for question in questions:
				answer = self.getAnswerForMemberAndQuestion(aMember, question)
				if answer: 
					parts.append(answer.displayStringShort())
				else:
					parts.append("")
			# about teller
			for question in memberQuestions:
				answer = aMember.getAnswerForQuestion(question)
				if answer:
					parts.append(answer.displayStringShort())
				else:
					parts.append("")
			# pad spaces for character questions
			for question in characterQuestions:
				parts.append("")
		for character in characters:
			parts.append("\n%s" % index)
			parts.append(self.title)
			parts.append(character.name)
			# questions about entry
			for question in questions:
				answer = self.getAnswerForCharacterAndQuestion(character, question)
				if answer: 
					parts.append(answer.displayStringShort())
				else:
					parts.append("")
			# pad spaces for member questions
			for question in memberQuestions:
				parts.append("")
			# about character attributed to
			for question in characterQuestions:
				answer = character.getAnswerForQuestion(question)
				if answer:
					parts.append(answer.displayStringShort())
				else:
					parts.append("")
		parts.append("\n")
		return CleanUpCSV(parts)
	
	def PrintText(self, member):
		typeToShow = DisplayTypeForEntryType(self.type).capitalize()
		creator = self.memberNickNameOrCharacterName()
		time = TimeDisplay(self.published, member)
		return '<p><b>%s</b>: %s [%s, %s]</p><div style="padding: 0px 16px 0px 16px;">%s</div></p><hr>\n\n' % (typeToShow, self.title, creator, time, self.text_formatted)
		
	def MemberWantsToSeeMyTypeInLocation(self, member, location):
		i = 0
		for type in ENTRY_TYPES:
			if type == self.type: 
				if member.getEntryTypeForLocationAndIndex(location, i):
					return True
				else:
					return False
				break
			i += 1
		return False
	
	# SEARCH
	
	def satisfiesSearch(self, search, refs):
		pass
	
# ============================================================================================
# ============================================================================================
class TextVersion(db.Model): 
# ============================================================================================
# version of text portion of entry (for audit trail and for backtracking)
# parent: entry; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="versions_to_rakontu")
	entry = db.ReferenceProperty(Entry, required=True, collection_name="versions_to_entries")
	created = TzDateTimeProperty(auto_now_add=True)

	title = db.StringProperty(indexed=False)
	text = db.TextProperty(default=NO_TEXT_IN_ENTRY)
	text_formatted = db.TextProperty()
	text_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_version"], self.key().name())

	def getKeyName(self):
		return self.key().name()
	
# ============================================================================================
# ============================================================================================
class Link(db.Model): 
# ============================================================================================
# connection between entries, types: related, retold, reminded, responded, included
# parent: entry (parent is always entry FROM); URL lookup: none needed, never looked up directly
# ============================================================================================

	type = db.StringProperty(choices=LINK_TYPES, required=True) 
	# how links go: 
	#	related: any entry to any entry
	#	retold: story to story
	# 	reminded: story or resource to story
	#   responded: invitation to story
	#	included: collage to story
	#   referenced: pattern to saved search - note, this is the only non-entry link item, and it is ALWAYS itemTo
	itemFrom = db.ReferenceProperty(None, collection_name="links_to_entries_incoming", required=True)
	itemTo = db.ReferenceProperty(None, collection_name="links_to_entries_outgoing", required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="links_to_rakontu")
	creator = db.ReferenceProperty(Member, collection_name="links_to_members")
	
	# links cannot be in draft mode and cannot be entered in batch mode
	flaggedForRemoval = db.BooleanProperty(default=False)
	flagComment = db.StringProperty(indexed=False)
	
	created = TzDateTimeProperty(auto_now_add=True)
	published = TzDateTimeProperty()
	inBatchEntryBuffer = db.BooleanProperty(default=False)
	
	comment = db.StringProperty(default="", indexed=False)
	
	entryNudgePointsWhenPublished = db.ListProperty(int, default=[0] * NUM_NUDGE_CATEGORIES, indexed=False)
	entryActivityPointsWhenPublished = db.IntegerProperty(default=0, indexed=False)
	
	# IMPORTANT METHODS
	
	def publish(self):
		self.published = datetime.now(pytz.utc)
		if self.itemTo.isEntry():
			self.itemTo.recordAction("added", self, "Link")
		self.itemFrom.recordAction("added", self, "Link")
		for i in range(NUM_NUDGE_CATEGORIES):
			if self.rakontu.nudgeCategoryIndexHasContent(i):
				self.entryNudgePointsWhenPublished[i] = self.itemFrom.nudgePoints[i]
		self.entryActivityPointsWhenPublished = self.itemFrom.activityPoints
		self.creator.nudgePoints = self.itemFrom.rakontu.getMemberNudgePointsForEvent("adding %s link" % self.type)
		# caller must do puts
		
	# MEMBERS
		
	def attributedToMember(self):
		return True
	
	# DISPLAY
		
	def getImageLinkForType(self):
		return ImageLinkForLink(-1) # -1 means don't put a tooltip count
	
	def displayString(self):
		result = '%s &gt; %s &gt; %s' % (self.itemFrom.linkString(), DisplayTypeForLinkType(self.type), self.itemTo.linkString())
		if self.comment:
			result += ", (%s)" % self.comment
		return result
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return self.displayString()
	
	def linkStringWithFromItem(self):
		result = self.itemFrom.linkString()
		if self.comment:
			result += ", (%s)" % self.comment
		return result
	
	def PrintText(self, member):
		linkString = TERMS["term_link"].capitalize()
		type = DisplayTypeForLinkType(self.type)
		name = self.creator.nickname
		time = TimeDisplay(self.published, member)
		return '<p><b>%s</b>: %s &gt; %s &gt; %s [%s, %s]</p><div style="padding: 0px 16px 0px 16px;">%s</div></p><hr>\n\n' % \
			(linkString, self.itemFrom.title, type, self.itemTo.title, name, time, self.comment)

	def MemberWantsToSeeMyTypeInLocation(self, member, location):
		return member.getAnnotationAnswerLinkTypeForLocationAndIndex(location, ANNOTATION_ANSWER_LINK_TYPES_LINK_INDEX)
	
	def getEntryNudgePointsWhenPublishedForExistAndShowOptions(self, exist, show):
		result = 0
		for i in range(NUM_NUDGE_CATEGORIES):
			if exist[i] and show[i]:
				result += self.entryNudgePointsWhenPublished[i]
		return result
	
# ============================================================================================
# ============================================================================================
class Attachment(db.Model):	
# ============================================================================================
# file attachments to entries
# parent: entry; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	created = TzDateTimeProperty(auto_now_add=True)
	entry = db.ReferenceProperty(Entry, collection_name="attachments_to_entries")
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="attachments_to_rakontu")

	name = db.StringProperty(default=UNTITLED_ATTACHMENT_NAME, indexed=False)
	mimeType = db.StringProperty(indexed=False) # from ACCEPTED_ATTACHMENT_MIME_TYPES
	fileName = db.StringProperty(indexed=False) # as uploaded
	data = db.BlobProperty() 
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s">%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.fileName)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_attachment"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_attachment"], self.getKeyName())
	
	def isImage(self):
		return self.mimeType == "image/jpeg" or self.mimeType == "image/png"
	
	def imageEmbed(self):
		return '<img src="/%s/%s?%s=%s">' % (DIRS["dir_visit"], URLS["url_image"], URL_IDS["url_query_attachment"], self.getKeyName())
	
	def attachmentEmbed(self):
		return '<a href="/%s?%s=%s">%s</a>' %(URLS["url_attachment"], URL_IDS["url_query_attachment"], self.getKeyName(), self.fileName)
	
# ============================================================================================
# ============================================================================================
class Annotation(db.Model):	
# ============================================================================================
# things people said about entries, types: tag set, comment, request, nudge
# parent: entry; URL lookup: id property
# ============================================================================================

	id = db.StringProperty(required=True)
	type = db.StringProperty(choices=ANNOTATION_TYPES, required=True)
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="annotations_to_rakontu")
	entry = db.ReferenceProperty(Entry, required=True, collection_name="annotations_to_entry") 
	creator = db.ReferenceProperty(Member, collection_name="annotations_to_member") 
	
	inBatchEntryBuffer = db.BooleanProperty(default=False) # in the process of being imported, not "live" yet
	flaggedForRemoval = db.BooleanProperty(default=False)
	flagComment = db.StringProperty(indexed=False)
	
	shortString = db.StringProperty(indexed=False) # comment/request subject, nudge comment
	
	longString = db.TextProperty() # comment/request body
	longString_formatted = db.TextProperty()
	longString_format = db.StringProperty(default=DEFAULT_TEXT_FORMAT, indexed=False)
	
	tagsIfTagSet = db.StringListProperty(default=[""] * NUM_TAGS_IN_TAG_SET, indexed=False)
	valuesIfNudge = db.ListProperty(int, default=[0] * NUM_NUDGE_CATEGORIES, indexed=False)
	typeIfRequest = db.StringProperty(choices=REQUEST_TYPES)
	completedIfRequest = db.BooleanProperty(default=False)
	completionCommentIfRequest = db.StringProperty()

	collectedOffline = db.BooleanProperty(default=False, indexed=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="annotations_to_liaisons")
	character = db.ReferenceProperty(Character, default=None, collection_name="annotations_to_characters")

	collected = TzDateTimeProperty(default=None, indexed=False)
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True, indexed=False)
	published = TzDateTimeProperty()
	
	entryNudgePointsWhenPublished = db.ListProperty(int, default=[0] * NUM_NUDGE_CATEGORIES, indexed=False)
	entryActivityPointsWhenPublished = db.IntegerProperty(default=0, indexed=False)
	
	def isAnnotation(self):
		return True
	
	def getClassName(self):
		return self.__class__.__name__
	
	def isCommentOrRequest(self):
		return self.type == "comment" or self.type == "request"
	
	def entryKey(self):
		try:
			if self.entry:
				return self.entry.key()
		except:
			return None
		else:
			return None
		
	def entryLinkString(self):
		try:
			if self.entry:
				return self.entry.linkString()
		except:
			return None
		else:
			return None
		
	def entryPublished(self):
		try:
			if self.entry:
				return self.entry.published
		except:
			return None
		else:
			return None
		
	def entryFlaggedForRemoval(self):
		try:
			if self.entry:
				return self.entry.flaggedForRemoval
		except:
			return None
		else:
			return None
	
	# IMPORTANT METHODS
	
	def publish(self):
		self.published = datetime.now(pytz.utc)
		self.entry.recordAction("added", self, "Annotation")
		for i in range(NUM_NUDGE_CATEGORIES):
			if self.rakontu.nudgeCategoryIndexHasContent(i):
				self.entryNudgePointsWhenPublished[i] = self.entry.nudgePoints[i]
		self.entryActivityPointsWhenPublished = self.entry.activityPoints
		self.creator.nudgePoints += self.rakontu.getMemberNudgePointsForEvent("adding %s" % self.type)
		# caller must do puts

	# TYPE
	
	def isComment(self):
		return self.type == "comment"
	
	def isRequest(self):
		return self.type == "request"
	
	def isNudge(self):
		return self.type == "nudge"
	
	# NUDGE SYSTEM
	
	def totalNudgePoints(self):
		result = 0
		for value in self.valuesIfNudge:
			result += value
		return result
	
	def totalNudgePointsAbsolute(self):
		result = 0
		for value in self.valuesIfNudge:
			result += abs(value)
		return result
	
	# MEMBERS
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else:
			return self.creator.nickname
		
	# DISPLAY
		
	def typeAsURL(self):
		return URLForAnnotationType(self.type)
	
	def typeForDisplay(self):
		return DisplayTypeForAnnotationType(self.type)
	
	def displayString(self, includeType=True, showDetails=True):
		if self.type == "comment":
			if self.shortString:
				return self.shortString
			elif self.longString_formatted:
				return self.longString_formatted
			else:
				return "no content"
		if self.type == "request":
			if self.shortString:
				if includeType:
					return "%s (%s)" % (self.shortString, self.typeIfRequest)
				else:
					return self.shortString
			elif self.longString_formatted:
				if includeType:
					return "%s (%s)" % (self.longString_formatted, self.typeIfRequest)
				else:
					return self.longString_formatted
			else:
				return "no content"
		elif self.type == "tag set":
			tagsToReport = []
			for tag in self.tagsIfTagSet:
				if len(tag):
					tagsToReport.append(tag)
			return  ", ".join(tagsToReport)
		elif self.type == "nudge":
			resultString = self.displayStringForNudgeWithoutComment(showDetails)
			if showDetails and self.shortString:
				resultString += " (%s)" % self.shortString
			return resultString
		
	def displayStringForNudgeWithoutComment(self, showDetails):
		result = []
		for i in range(NUM_NUDGE_CATEGORIES):
			if self.rakontu.nudgeCategoryIndexHasContent(i):
				if showDetails:
					if self.valuesIfNudge[i] != 0:
						result.append("%s %s" % (self.valuesIfNudge[i], self.rakontu.nudgeCategories[i]))
				else:
					result.append("%s" % (self.valuesIfNudge[i]))
		resultString = ", ".join(result)
		return resultString
		
	def displayStringShortAndWithoutTags(self):
		return self.displayString(includeType=False)
	
	def PrintText(self, member):
		name = self.memberNickNameOrCharacterName()
		time = TimeDisplay(self.published, member)
		type = DisplayTypeForAnnotationType(self.type).capitalize()
		displayString = self.displayString(showDetails=True)
		nudgeString = self.displayStringForNudgeWithoutComment(showDetails=True)
		if self.isCommentOrRequest():
			return '<p><b>%s</b>: %s [%s, %s, %s]<div style="padding: 0px 16px 0px 16px;">%s</div></p><hr>\n\n' % \
				(type, self.shortString, self.entry.title, name, time, self.longString_formatted)
		elif self.type == "nudge":
			return '<p><b>%s</b>: %s [%s, %s, %s]<div style="padding: 0px 16px 0px 16px;">%s</div></p><hr>\n\n' % \
				(type, nudgeString, self.entry.title, name, time, self.shortString)
		else:
			return '<p><b>%s</b>: %s [%s, %s, %s]</p><hr>\n\n' % (type, displayString, self.entry.title, name, time)
		
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self, showDetails=True):
		if self.type == "comment" or self.type == "request":
			return '<a href="%s?%s" %s>%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.getTooltipText(), self.shortString)
		else:
			return self.displayString(showDetails=showDetails)
		
	def getTooltipText(self):
		if self.longString_formatted:
			return'title="%s (%s)"' % (stripTags(self.longString_formatted[:TOOLTIP_LENGTH]), self.memberNickNameOrCharacterName())
		else:
			return ""
	
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_read_annotation"])

	def urlQuery(self):
		return "%s=%s" % (URL_IDS["url_query_annotation"], self.key().name())
		
	def linkStringWithEntryLink(self, showDetails=True):
		return "%s %s %s" % (self.linkString(showDetails=showDetails), TERMS["term_for"], self.entry.linkString())
		
	def getImageLinkForType(self):
		return ImageLinkForAnnotationType(self.type, -1) # -1 means don't put a count tooltip
	
	def MemberWantsToSeeMyTypeInLocation(self, member, location):
		i = 0
		for type in ANNOTATION_ANSWER_LINK_TYPES:
			if type == self.type: 
				if  member.getAnnotationAnswerLinkTypeForLocationAndIndex(location, i):
					return True
				break
			i += 1
		return False

	def getEntryNudgePointsWhenPublishedForExistAndShowOptions(self, exist, show):
		result = 0
		for i in range(NUM_NUDGE_CATEGORIES):
			if exist[i] and show[i]:
				result += self.entryNudgePointsWhenPublished[i]
		return result
	
# ============================================================================================
# ============================================================================================
class Help(db.Model): 
# ============================================================================================
# context-sensitive help string - appears as title hover on icon 
# no parent
# ============================================================================================

	type = db.StringProperty() # info, tip, caution
	name = db.StringProperty() # links to name in template
	text = db.StringProperty(indexed=False) # text to show user (plain text)
	
	def cleanedUpName(self):
		return self.name.replace("_", " ").capitalize()
	
# ============================================================================================
# ============================================================================================
class Skin(db.Model): 
# ============================================================================================
# style sets to change look of each Rakontu
# no parent
# ============================================================================================

	name = db.StringProperty(required=True) 
	
	font_general = db.StringProperty(indexed=False) # on everything except buttons and headers
	font_top = db.StringProperty(indexed=False)
	font_menus = db.StringProperty(indexed=False)
	font_buttons = db.StringProperty(indexed=False)
	font_headers = db.StringProperty(indexed=False)
	font_inputs = db.StringProperty(indexed=False)
	
	color_background_general = db.StringProperty(indexed=False) # on all pages
	color_text_plain = db.StringProperty(indexed=False) # plain text - usually black
	
	color_background_link_hover = db.StringProperty(indexed=False) # light-up effect for links
	color_text_link = db.StringProperty(indexed=False) # links in text
	color_text_link_hover = db.StringProperty(indexed=False) # link light-up on hover (usually white, constrasts with background_link_hover)

	color_background_excerpt = db.StringProperty(indexed=False) # behind story texts and other "highlighted" boxes
	color_text_excerpt = db.StringProperty(indexed=False) # text color in excerpts
	
	color_background_entry = db.StringProperty(indexed=False) # to indicate the user is entering data
	color_text_entry = db.StringProperty(indexed=False) # text color on entry areas
	
	color_background_table_header = db.StringProperty(indexed=False) # to make table headers stand out a bit
	color_text_table_header = db.StringProperty(indexed=False) # text color on table headers
	
	color_background_menus = db.StringProperty(indexed=False) # menu backgrounds
	color_text_menus = db.StringProperty(indexed=False) # text color in menus
	color_background_menus_hover =  db.StringProperty(indexed=False) # menu backgrounds when hovering over
	color_text_menus_hover = db.StringProperty(indexed=False) # text color in menus when hovering over
		
	color_background_grid_top = db.StringProperty(indexed=False) # entry grid on home page, annotation grid on entry page
	color_background_grid_bottom = db.StringProperty(indexed=False) # same but on bottom of grid (should be "faded" from top)
	color_text_grid = db.StringProperty(indexed=False) # text in grid (not links, those are controlled by color_text_link)
	
	color_background_inputs = db.StringProperty(indexed=False) # text boxes, drop-down boxes
	color_text_inputs = db.StringProperty(indexed=False)
		
	color_background_button = db.StringProperty(indexed=False) # button at bottom of pages
	color_background_button_hover = db.StringProperty(indexed=False) # when button is hovered over
	color_text_buttons = db.StringProperty(indexed=False) # text color on buttons
	color_text_buttons_hover = db.StringProperty(indexed=False)
		
	color_border_normal = db.StringProperty(indexed=False) # around everything
	color_border_input_hover = db.StringProperty(indexed=False) # lights up when mouse is over entries (text, drop-down box)
	color_border_image = db.StringProperty(indexed=False) # border around images
		
	color_text_h1 = db.StringProperty(indexed=False) # h1 text
	color_text_h2 = db.StringProperty(indexed=False) # h2 text
	color_text_h3 = db.StringProperty(indexed=False) # h3 text
	color_text_label_hover = db.StringProperty(indexed=False) # color of labels, like checkbox names
	
	def getPropertiesAsDictionary(self):
		result = {}
		properties = Skin.properties()
		for key in properties.keys():
			value = getattr(self, key)
			result[key] = value
		return result
	
	def asText(self):
		lines = []
		properties = Skin.properties()
		for key in properties.keys():
			if key.find("font_") >= 0 or key.find("color_") >= 0:
				lines.append("%s=%s" % (key, getattr(self, key)))
		lines.sort()
		return "\n".join(lines)

# ============================================================================================
# ============================================================================================
class Export(db.Model):
# ============================================================================================
# data prepared for export, in XML or CSV or HTML format
# no parent
# ============================================================================================
	
	rakontu = db.ReferenceProperty(Rakontu, required=True, collection_name="export_to_rakontu")
	type = db.StringProperty()
	fileFormat = db.StringProperty(indexed=False)
	created = TzDateTimeProperty(auto_now_add=True, indexed=False)
	data = db.TextProperty()
	
	def getKeyName(self):
		return self.key().name()
	
	def linkString(self):
		return '<a href="%s?%s">%s</a>' % (self.urlWithoutQuery(), self.urlQuery(), self.type)
		
	def linkURL(self):
		return '%s?%s' % (self.urlWithoutQuery(), self.urlQuery())
		
	def urlWithoutQuery(self):
		return "/%s/%s" % (DIRS["dir_visit"], URLS["url_export"])

	def urlQuery(self):
		if self.fileFormat == "csv":
			return "%s=%s" % (URL_IDS["url_query_export_csv"], self.getKeyName())
		elif self.fileFormat == "txt":
			return "%s=%s" % (URL_IDS["url_query_export_txt"], self.getKeyName())
		elif self.fileFormat == "xml":
			return "%s=%s" % (URL_IDS["url_query_export_xml"], self.getKeyName())

# ============================================================================================
# ============================================================================================
# SOME DB FETCHING METHODS - all get and fetch calls are in this file
# ============================================================================================
# ============================================================================================


def AllRakontus():
	return Rakontu.all().fetch(FETCH_NUMBER)

def AllHelps():
	return Help.all().fetch(FETCH_NUMBER)

def NumHelps():
	return Help.all().count()

def HaveHelps():
	return Help.all().count() > 0

def AllSkins():
	return Skin.all().fetch(FETCH_NUMBER)

def NumSkins():
	return Skin.all().count()

def GetSkinByName(name):
	return Skin.all().filter("name = ", name).get()

def AllSystemQuestions():
	return Question.all().filter("rakontu = ", None).fetch(FETCH_NUMBER)

def NumSystemQuestions():
	return Question.all().filter("rakontu = ", None).count()

def SystemQuestionsOfType(type):
	return Question.all().filter("rakontu = ", None).filter("refersTo = ", type).fetch(FETCH_NUMBER)

def SystemEntriesOfType(type):
	return Entry.all().filter("rakontu = ", None).filter("type = ", type).fetch(FETCH_NUMBER)

def HaveSystemResources():
	return Entry.all().filter("rakontu = ", None).filter("type = ", "resource").count() > 0

def ActiveMemberForUserIDAndRakontu(userID, rakontu):
	return Member.all().filter("googleAccountID = ", userID).filter("rakontu = ", rakontu).filter("active = ", True).get()

def pendingMemberForEmailAndRakontu(email, rakontu):
	return PendingMember.all().filter("email = ", email).filter("rakontu = ", rakontu).get()

def helpLookup(name, type):  
	return Help.all().filter("name = ", name).filter("type = ", type).get()

def helpTextLookup(name, type):
	match = Help.all().filter("name = ", name).filter("type = ", type).get()
	if match:
		return match.text
	else: 
		return None
	
def ItemsMatchingViewOptionsForMemberAndLocation(member, location, entry=None, memberToSee=None, character=None):
	rakontu = member.rakontu
	viewOptions = member.getViewOptionsForLocation(location)
	startTime = viewOptions.getStartTime()
	endTime = viewOptions.endTime 
	entryTypeBooleans = viewOptions.entryTypes
	entryTypes = []
	for i in range(len(ENTRY_TYPES)):
		if entryTypeBooleans[i]:
			entryTypes.append(ENTRY_TYPES[i])
	annotationTypeBooleans = viewOptions.annotationAnswerLinkTypes
	annotationTypes = []
	for i in range(len(ANNOTATION_ANSWER_LINK_TYPES)):
		if annotationTypeBooleans[i]:
			annotationTypes.append(ANNOTATION_ANSWER_LINK_TYPES[i]) 
	if location == "home":
		itemsToStart = member.rakontu.browseEntries(startTime, endTime, entryTypes)
		considerNudgeFloor = True
		considerSearch = True
	elif location == "entry":
		itemsToStart = entry.browseItems(startTime, endTime, annotationTypes)
		considerNudgeFloor = False
		considerSearch = False
	elif location == "member":
		itemsToStart = memberToSee.browseItems(startTime, endTime, entryTypes, annotationTypes)
		considerNudgeFloor = False
		considerSearch = True
	elif location == "character":
		itemsToStart = character.browseItems(startTime, endTime, entryTypes, annotationTypes)
		considerNudgeFloor = False
		considerSearch = True
	# nudge floor
	itemsWithNudgeFloor = []
	exist, show = NudgeCategoriesExistAndShouldBeShownInContext(member, location)
	if considerNudgeFloor:
		for item in itemsToStart:
			if item.nudgePointsForExistAndShowOptions(exist, show) >= viewOptions.nudgeFloor:
				itemsWithNudgeFloor.append(item)
	else:
		itemsWithNudgeFloor.extend(itemsToStart)
	# search
	itemsWithSearch = []
	if considerSearch:
		search = viewOptions.search
		if search:
			entryRefs = search.getEntryQuestionRefs()
			creatorRefs = search.getCreatorQuestionRefs()
			for item in itemsWithNudgeFloor:
				if item.__class__.__name__ == "Entry":
					if item.satisfiesSearchCriteria(search, entryRefs, creatorRefs):
						itemsWithSearch.append(item)
				else: # if searching in member/character page, no annotations will show
					pass
		else:
			itemsWithSearch.extend(itemsWithNudgeFloor)
	else:
		itemsWithSearch.extend(itemsWithNudgeFloor)
	# limit
	itemsWithLimit = []
	overLimitWarning = None
	numItemsBeforeLimitTruncation = None
	considerLimit = True # in case of need later
	if considerLimit:
		limit = MAX_ITEMS_PER_GRID_PAGE # viewOptions.limitPerPage # in case of need later
		if len(itemsWithSearch) > limit:
			for i in range(limit):
				itemsWithLimit.append(itemsWithSearch[i])
			overLimitWarning = TERMS["term_too_many_items_warning"]
			numItemsBeforeLimitTruncation = len(itemsWithSearch)
		else:
			itemsWithLimit.extend(itemsWithSearch)
	else:
		itemsWithLimit.extend(itemsWithSearch)
	return (itemsWithLimit, overLimitWarning, numItemsBeforeLimitTruncation)

def NudgeCategoriesExistAndShouldBeShownInContext(member, location):
	exist = []
	show = []
	viewOptions = member.getViewOptionsForLocation(location)
	for i in range(NUM_NUDGE_CATEGORIES):
		exist.append(member.rakontu.nudgeCategoryIndexHasContent(i))
		show.append(viewOptions.nudgeCategories[i])
	return exist, show

def ShouldKeepAnswer(request, queryText, question):
	keepAnswer = False
	response = request.get(queryText)
	if (question.type == "nominal" or question.type == "ordinal"):
		if question.multiple:
			keepAnswer = False
			for choice in question.choices:
				if request.get("%s|%s" % (queryText, choice)) == "yes":
					keepAnswer = True
					break
		else: # single choice
			keepAnswer = len(response) > 0 and response != "None" and response != TERMS["term_choose"]
	else:		
		if question.type == "boolean":
			keepAnswer = queryText in request.params.keys()
		else:
			keepAnswer = len(response) > 0 and response != "None"
	return keepAnswer

def ProcessAttributionFromRequest(request, member):
	creator = None
	liaison = None
	dateCollected = None
	collectedOffline = request.get("collectedOffline") == "yes"
	if collectedOffline and member.isLiaison():
		if member.isManagerOrOwner():
			membersToConsider = member.rakontu.getActiveMembers()
		else:
			membersToConsider = member.rakontu.getActiveOfflineMembers()
		for aMember in membersToConsider:
			if request.get("offlineSource") == str(aMember.key()):
				creator = aMember
				break
		liaison = member
		dateCollected = parseDate(request.get("year"), request.get("month"), request.get("day"))
	else:
		creator = member
	if collectedOffline:
		attributionQueryString = "offlineAttribution"
	else:
		attributionQueryString = "attribution"
	if request.get(attributionQueryString) and request.get(attributionQueryString) != "member":
		characterKey = request.get(attributionQueryString)
		try:
			character = Character.get(characterKey)
		except:
			character = None
	else:
		character = None
	return (collectedOffline, creator, liaison, dateCollected, character)
		
# ============================================================================================
# ============================================================================================
# DATE AND TIME
# ============================================================================================
# ============================================================================================

def parseDate(yearString, monthString, dayString):
	if yearString and monthString and dayString:
		try:
			year = int(yearString)
			month = int(monthString) 
			day = int(dayString)
			date = datetime(year, month, day, tzinfo=pytz.utc)
			return date
		except:
			return datetime.now(tz=pytz.utc)
	return datetime.now(tz=pytz.utc)

def DjangoToPythonDateFormat(format):
	if DATE_FORMATS.has_key(format):
		return DATE_FORMATS[format]
	return "%B %d, %Y"

def DjangoToPythonTimeFormat(format):
	if TIME_FORMATS.has_key(format):
		return TIME_FORMATS[format]
	return "%I:%M %p"

def DateFormatStrings():
	result = {}
	for format in DATE_FORMATS.keys():
		result[format] = datetime.now().strftime(DATE_FORMATS[format])
	return result

def TimeFormatStrings():
	result = {}
	for format in TIME_FORMATS.keys():
		result[format] = datetime.now().strftime(TIME_FORMATS[format])
	return result

def TimeDisplay(whenUTC, member):
	if member and member.timeZoneName:
		timeZone = getTimeZone(member.timeZoneName)
		when = whenUTC.astimezone(timeZone)
		return "%s %s" % (stripZeroOffStart(when.strftime(DjangoToPythonTimeFormat(member.timeFormat))),
						(when.strftime(DjangoToPythonDateFormat(member.dateFormat))))
	else:
		return None
	
def stripZeroOffStart(text):
	if text[0] == "0":
		return text[1:]
	else:
		return text
	
def getTimeZone(timeZoneName):
	try:
		timeZone = memcache.get("tz:%s" % timeZoneName)
	except:
		timeZone = None
	if timeZone is None:
		timeZone = timezone(timeZoneName)
		memcache.add("tz:%s" % timeZoneName, timeZone, DAY_SECONDS)
	return timeZone

def ImageLinkForAnnotationType(type, number):
	if number >= 0:
		i = 0
		for aType in ANNOTATION_TYPES:
			if aType == type:
				if number > 1:
					typeToDisplay = ANNOTATION_TYPES_PLURAL_DISPLAY[i]
				else:
					typeToDisplay = ANNOTATION_TYPES_DISPLAY[i]
				break
			i += 1
		tooltip = 'title="%s %s"' % (number, typeToDisplay)
	else:
		tooltip = ""
	if type == "comment":
		name = TEMPLATE_TERMS["template_comment"]
		imageText = '<img src="/images/comments.png" alt="%s" title="%s" %s border="0">' % (name, name, tooltip)
	elif type == "request":
		name = TEMPLATE_TERMS["template_request"]
		imageText = '<img src="/images/requests.png" alt="%s" title="%s" %s border="0">' % (name, name, tooltip)
	elif type == "tag set":
		name = TEMPLATE_TERMS["template_tag_set"]
		imageText = '<img src="/images/tags.png" alt="%s" title="%s" %s border="0">' % (name, name, tooltip)
	elif type == "nudge":
		name = TEMPLATE_TERMS["template_nudge"]
		imageText = '<img src="/images/nudges.png" alt="%s" title="%s" %s border="0">' % (name, name, tooltip)
	return imageText

def ImageLinkForAnswer(number):
	if number >= 0:
		if number > 1:
			term = TERMS["term_answers"]
		else:
			term = TERMS["term_answer"]
		tooltip = 'title="%s %s"' % (number, term)
	else:
		tooltip = ""
	return'<img src="/images/answers.png" alt="answer" %s border="0">' % tooltip

def ImageLinkForLink(number):
	if number >= 0:
		if number > 1:
			term = TERMS["term_links"]
		else:
			term = TERMS["term_link"]
		tooltip = 'title="%s %s"' % (number, term)
	else:
		tooltip = ""
	return'<img src="/images/link.png" alt="link" title="link" %s border="0">' % tooltip

HTML_ESCAPES = {
 	"&": "&amp;",
 	'"': "&quot;",
 	"'": "&apos;",
 	">": "&gt;",
 	"<": "&lt;",  
 	 } 
  
def htmlEscape(text):  
	result = []  
	for character in text:  
		result.append(HTML_ESCAPES.get(character, character))  
	return "".join(result)
 
