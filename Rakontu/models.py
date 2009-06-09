﻿# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

from utils import *
 
# --------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------

DEVELOPMENT = True
FETCH_NUMBER = 1000

# community
NUM_NUDGE_CATEGORIES = 5
DEFAULT_MAX_NUDGE_POINTS_PER_ARTICLE = 10
DEFAULT_NUDGE_POINT_ACCUMULATIONS = [
									0, # time (doesn't apply here)
					 				4, # reading
					 				20, # telling
					 				5, # retelling
					 				5, # reminding
					 				10, # relating
					 				15, # including
					 				30, # responding
					 				2, # answering
					 				4, # tagging
					 				5, # commenting
					 				8, # requesting
					 				20, # nudging 
					 				]

DATE_FORMATS = {
			"j F Y": "%e %B %Y", # 3 January 2000
			"F j, Y": "%B %e, %Y", # January 3, 2000
			"j F": "%e %B", # 3 January
			"F j": "%B %e", # January 3
			"j/n/Y": "%d/%m/%Y", # 03/01/2000
			"n/j/Y": "%m/%d/%Y", # 01/03/2000
			}
TIME_FORMATS = {
			"h:i a": "%I:%M %p", #"5:00 pm", 
			"H:i": "%H:%M", #"17:00",
			}

# member
NO_NICKNAME_SET = "No nickname set"
MEMBER_TYPES = ["member", "on-line member", "off-line member", "liaison", "curator", "guide", "manager", "owner"]
HELPING_ROLE_TYPES = ["curator", "guide", "liaison"]
DEFAULT_ROLE_READMES = [
						"A curator pays attention to Rakontu's accumulated data. Curators add information, check for problems, create links, and in general maintain the vitality of the story bank.",
						"A guide pays attention to the Rakontu's on-line human community. Guides answer questions, write tutorials, encourage people to tell and use stories, create patterns, write and respond to requests, set up and run exercises, and in general maintain the vitality of the on-line member community.",
						"A liaison guides stories and other information over the barrier between on-line and off-line worlds. Liaisons conduct external interviews and add the stories people tell in them, read stories to people and gather comments, nudges, and other annotations, and in general make the system work for both on-line and off-line community members."]
GOVERNANCE_ROLE_TYPES = ["member", "manager", "owner"]
ACTIVITIES_GERUND = ["time", \
					   	 "reading", \
						 "telling", "retelling", "reminding", "relating", "including", "responding", \
						 "answering question", "tagging", "commenting", "requesting", "nudging"]
ACTIVITIES_VERB = ["time", \
					   	 "read", \
						 "told", "retold", "reminded", "related", "included", "responded", \
						 "question answered about", "tagged", "commented", "requested", "nudged"]

# articles
ARTICLE_TYPES = ["story", "pattern", "collage", "invitation", "resource"]
LINK_TYPES = ["retold", "reminded", "responded", "related", "included"]
ACCEPTED_ATTACHMENT_FILE_TYPES = ["jpg", "png", "pdf", "doc", "txt", "mpg", "mp3", "html", "zip"]
ACCEPTED_ATTACHMENT_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf", "application/msword", "text/plain", "video/mpeg", "audio/mpeg", "text/html", "application/zip"]

# annotations
ANNOTATION_TYPES = ["tag set", "comment", "request", "nudge"]
ANNOTATION_TYPES_URLS = ["tagset", "comment", "request", "nudge"]
NUDGE_TYPES = ["appropriateness", "importance", "utility", "utility custom 1", "utility custom 2", "utility custom 3"]
ENTRY_TYPES = ["story", "pattern", "collage", "invitation", "resource", "answer", "tag set", "comment", "request", "nudge"]
ENTRY_TYPES_URLS = ["story", "pattern", "collage", "invitation", "resource", "answer", "tagset", "comment", "request", "nudge"]
STORY_ENTRY_TYPE_INDEX = 0
ANSWERS_ENTRY_TYPE_INDEX = 5

# browsing
MINUTE_SECONDS = 60
HOUR_SECONDS = 60 * MINUTE_SECONDS
DAY_SECONDS = 24 * HOUR_SECONDS
WEEK_SECONDS = 7 * DAY_SECONDS
MONTH_SECONDS = 30 * DAY_SECONDS
YEAR_SECONDS = 365 * DAY_SECONDS
TIME_UNIT_STRINGS = {"minute": MINUTE_SECONDS, 
					"hour": HOUR_SECONDS,
					"day": DAY_SECONDS,
					"week": WEEK_SECONDS,
					"month": MONTH_SECONDS,
					"year": YEAR_SECONDS,}
TIME_FRAMES = ["minute", "hour", "day", "week", "month", "year"]
DEFAULT_ACTIVITY_POINTS_PER_EVENT = [
									-1, # time
					 				5, # reading
					 				2, # telling  
					 				2, # retelling
					 				2, # reminding
					 				2, # relating
					 				2, # including 
					 				2, # responding
					 				2, # answering
					 				10, # tagging
					 				10, # commenting
					 				20, # requesting
					 				6, # nudging 
					 				]

HISTORY_ACTION_TYPES = ["read", "added"]
HISTORY_REFERENT_TYPES = ["story", "pattern", "collage", "invitation", "resource", \
						  "retold link", "reminded link", "related link", "included link", \
						  "answer", "tag set", "comment", "request", "nudge"]
DEFAULT_ACTIVITY_ACCUMULATIONS = {"story": 1, "pattern": 1, "collage": 1, "invitation": 1, "resource": 1, \
						  "retold link": 3, "reminded link": 3, "related link": 3, "included link": 3, \
						  "answer": 3, "tag set": 10, "comment": 10, "request": 10, "nudge": 10}

# querying
QUERY_TYPES = ["free text", "tags", "answers", "members", "activities", "links"]
QUERY_TARGETS = ["stories", "patterns", "collages", "invitations", "resources", "articles", "answers", "tags", "comments", "requests", "nudge comments"]
BOOLEAN_CHOICES = ["ALL", "ANY"]
RECENT_TIME_FRAMES = ["last hour", "last day", "last week", "last month", "last six months", "last year", "ever"]

# questions 
QUESTION_REFERS_TO = ["story", "pattern", "collage", "invitation", "resource", "member"]
QUESTION_REFERS_TO_PLURAL = ["stories", "patterns", "collages", "invitations", "resources", "members"]
QUESTION_TYPES = ["boolean", "text", "ordinal", "nominal", "value"]


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

# --------------------------------------------------------------------------------------------
# Community
# --------------------------------------------------------------------------------------------

class Community(db.Model):
	""" Preferences and settings for the whole community.
		There can be multiple communities within one Rakontu installation.
	
	Properties
		name:					The name that appears on all pages.
		tagline:				Very short description that comes after the community name on the top of the page.
		description:			Some text that describes the community. 
		etiquetteStatement:		This is just some extra text in case they want to say how people should behave.
		welcomeMessage:			Extra text a new member will see.
		image:					Picture to show on community page.
		
		nudgePointsPerActivity:	A number for each type of activity (ACTIVITIES_GERUND) denoting how many
								points the member accumulates for doing it.
		maxNudgePointsPerArticle:	How many nudge points a member is allowed to place (maximally) on any article.
		allowCharacter:	Whether members are allowed to enter things with
								a character marked. One entry per type of thing (ENTRY_TYPES)
		nudgeCategories:		Names of nudge categories. Up to five allowed.
		roleReadmes:			Texts all role members read before taking on a role.
								One text per helping role type.
		roleAgreements:			Whether the user is asked to click a checkbox before taking on a role
								to show that they agree with the terms of the role. (Social obligation only.)
		maxNumAttachments:		How many attachments are allowed per article.
								May be useful to keep the database from getting out of hand.
	"""
	name = db.StringProperty()
	tagline = db.StringProperty()
	description = db.TextProperty()
	description_formatted = db.TextProperty()
	description_format = db.StringProperty(default="plain text")
	etiquetteStatement = db.TextProperty()
	etiquetteStatement_formatted = db.TextProperty()
	etiquetteStatement_format = db.StringProperty(default="plain text")
	welcomeMessage = db.TextProperty()
	welcomeMessage_formatted = db.TextProperty()
	welcomeMessage_format = db.StringProperty(default="plain text")
	image = db.BlobProperty(default=None)
	
	defaultTimeZoneName = db.StringProperty(default="US/Eastern")
	defaultTimeFormat = db.StringProperty(default="h:i a")
	defaultDateFormat = db.StringProperty(default="F j, Y")
	
	created = TzDateTimeProperty(auto_now_add=True)
	lastPublish = TzDateTimeProperty(default=None)
	firstPublish = TzDateTimeProperty(default=None)
	firstPublishSet = db.BooleanProperty(default=False)
	
	nudgePointsPerActivity = db.ListProperty(int, default=DEFAULT_NUDGE_POINT_ACCUMULATIONS)
	maxNudgePointsPerArticle = db.IntegerProperty(default=DEFAULT_MAX_NUDGE_POINTS_PER_ARTICLE)
	allowCharacter = db.ListProperty(bool, default=[True,True,True,True,True,True,True,True,True,True])
	nudgeCategories = db.StringListProperty(default=["appropriate", "important", "useful to new members", "useful for resolving conflicts", "useful for understanding"])
	roleReadmes = db.ListProperty(db.Text, default=[db.Text(DEFAULT_ROLE_READMES[0]), db.Text(DEFAULT_ROLE_READMES[1]), db.Text(DEFAULT_ROLE_READMES[2])])
	roleReadmes_formatted = db.ListProperty(db.Text, default=[db.Text(""), db.Text(""), db.Text("")])
	roleReadmes_formats = db.StringListProperty(default=["plain text", "plain text", "plain text"])
	roleAgreements = db.ListProperty(bool, default=[False, False, False])
	maxNumAttachments = db.IntegerProperty(choices=[0,1,2,3,4,5], default=3)
	
	def getOfflineMembers(self):
		return Member.all().filter("community = ", self.key()).filter("isOnlineMember = ", False).fetch(FETCH_NUMBER)
	
	# articles
	
	def getNonDraftArticles(self):
		return Article.all().filter("community = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getNonDraftArticlesOfType(self, type):
		return Article.all().filter("community = ", self.key()).filter("draft = ", False).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def getMemberForGoogleAccountId(self, id):
		return Member.all().filter("community = ", self.key()).filter("googleAccountID = ", id).fetch(1)
		
	def allowsAtLeastTwoAttachments(self):
		return self.maxNumAttachments >= 2
	
	def allowsAtLeastThreeAttachments(self):
		return self.maxNumAttachments >= 3
	
	def allowsAtLeastFourAttachments(self):
		return self.maxNumAttachments >= 4
	
	def allowsFiveAttachments(self):
		return self.maxNumAttachments == 5
	
	def maxNumAttachmentsAsText(self):
		if self.maxNumAttachments == 1:
			return "one"
		elif self.maxNumAttachments == 2:
			return "two"
		elif self.maxNumAttachments == 3:
			return "three"
		elif self.maxNumAttachments == 4:
			return "four"
		elif self.maxNumAttachments == 5:
			return "five"
	
	# community level questions and answers
	
	def getPendingMembers(self):
		return PendingMember.all().filter("community = ", self.key()).fetch(FETCH_NUMBER)

	def getMemberQuestions(self):
		return Question.all().filter("community = ", self.key()).filter("refersTo = ", "member").fetch(FETCH_NUMBER)
	
	def getQuestions(self):
		return Question.all().filter("community = ", self.key()).fetch(FETCH_NUMBER)
	
	def getQuestionsOfType(self, type):
		return Question.all().filter("community = ", self.key()).filter("refersTo = ", type).fetch(FETCH_NUMBER)
		
	def hasQuestionWithSameTypeAndName(self, question):
		allQuestions = self.getQuestions()
		for aQuestion in allQuestions:
			if aQuestion.refersTo == question.refersTo and aQuestion.name == question.name:
				return True
		return False
	
	def AddCopyOfQuestion(self, question):
		newQuestion = Question(
							   refersTo=question.refersTo,
							   name=question.name,
							   text=question.text,
							   type=question.type,
							   choices=question.choices,
							   help=question.help,
							   useHelp=question.useHelp,
							   multiple=question.multiple,
							   community=self)
		newQuestion.put()
	
	def getActiveMembers(self):
		return Member.all().filter("community = ", self.key()).filter("active = ", True).fetch(FETCH_NUMBER)
	
	def getInactiveMembers(self):
		return Member.all().filter("community = ", self.key()).filter("active = ", False).fetch(FETCH_NUMBER)
	
	def hasMemberWithGoogleEmail(self, email):
		members = self.getActiveMembers()
		for member in members:
			if member.googleAccountEmail == email:
				return True
		return False
	
	def getManagers(self):
		return Member.all().filter("community = ", self.key()).filter("governanceType = ", "manager").fetch(FETCH_NUMBER)
	
	def getOwners(self):
		return Member.all().filter("community = ", self.key()).filter("governanceType = ", "owner").fetch(FETCH_NUMBER)
	
	def memberIsOnlyOwner(self, member):
		owners = self.getOwners()
		if len(owners) == 1 and owners[0].key() == member.key():
			return True
		return False

	def getNudgePointsPerActivityForActivityName(self, activity):
		i = 0
		for anActivity in ACTIVITIES_GERUND:
			if anActivity == activity:
				return self.nudgePointsPerActivity[i]
			i += 1
		return 0
	
	def getCommunityLevelViewingPreferences(self):
		return ViewingPreferences.all().filter("community = ", self.key()).filter("owner = ", self.key()).fetch(FETCH_NUMBER)

	def getCharacters(self):
		return Character.all().filter("community = ", self.key()).fetch(FETCH_NUMBER)
	
	def hasAtLeastOneCharacterEntryAllowed(self, entryTypeIndex):
		return len(self.getCharacters()) > 0 or self.allowCharacter[entryTypeIndex]
	
# --------------------------------------------------------------------------------------------
# Question 
# --------------------------------------------------------------------------------------------

class Question(db.Model):
	""" Questions asked about the community, a member, or an article.
	
	Properties
		community:			The Rakontu community this question belongs to.
							If None, is in a global list communities can copy from. (??)
		refersTo:			What the question is in reference to: an article (story, pattern, collage, invitation, resource), 
							community, or member.
		
		type:				One of boolean, text, ordinal, nominal, value.
		lengthIfText:		How long is allowed for a text answer.
		minIfValue:			Minimum value allowed, if value.
		maxIfValue:			Maximum value allowed, if value.
		responseIfBoolean:	What the checkbox should say if the response is positive.
		options:			Options for display. Not using this field, saving in case of need later.
							Replaced "required" field which I got rid of.
		multiple:			Whether multiple answers are allowed.
		name:				Name to display in viewer or wherever a short handle is needed.
		text:				The actual text question asked. May be much longer.
		choices:			A list of strings with possible answers.
		
		help:				Explanatory text about how to answer the question.
		useHelp:			Appears to manager choosing question. Helps them decide when to use it.
	"""
	community = db.ReferenceProperty(Community, collection_name="questions_to_community")
	refersTo = db.StringProperty(choices=QUESTION_REFERS_TO, required=True)
	
	name = db.StringProperty(required=True, default="No name")
	text = db.StringProperty(required=True, default="No question text yet.")
	type = db.StringProperty(choices=QUESTION_TYPES, default="text")
	lengthIfText = db.IntegerProperty(default=40)
	minIfValue = db.IntegerProperty(default=0)
	maxIfValue = db.IntegerProperty(default=1000)
	responseIfBoolean = db.StringProperty(default="Yes")
	options = db.StringProperty(default="")
	multiple = db.BooleanProperty(default=False)
	choices = db.StringListProperty(default=["", "", "", "", "", "", "", "", "", ""])
	
	help = db.TextProperty()
	help_formatted = db.TextProperty()
	help_format = db.StringProperty(default="plain text")
	useHelp = db.TextProperty()
	useHelp_formatted = db.TextProperty()
	useHelp_format = db.StringProperty(default="plain text")
	
	created = TzDateTimeProperty(auto_now_add=True)
	
	def isOrdinalOrNominal(self):
		return self.type == "ordinal" or self.type == "nominal"
		
# --------------------------------------------------------------------------------------------
# Member
# --------------------------------------------------------------------------------------------

class Member(db.Model):
	""" A member is essentially the combination of a Google user and a Rakontu community,
		since a Google user can belong to more than one Rakontu community.
		Though members can also exist without Google accounts (those are off-line members).
	
	Properties
		community:			The community this member belongs to. 
		nickname:			The member's "handle" in the system. 
		googleAccountID:	UserID field from Google account. None if offline.
		googleAccountEmail:	The email with which the account was created. For display only.
		isOnlineMember:		Whether the member is online (has a Google account).
							Note that offline members cannot have helping roles or be managers or owners.
		active:				Flag set to false when members quit; so they can be reinstated easier.
		acceptsMessages:	Other members can send them messages, and they come through their email address.
		liaisonAccountID:	Can be permanently linked to a liaison. This is to help
							liaisons manage the offline members they have responsibility for.
							
		governanceType:		Whether they are a member, manager or owner.
		governanceView:		What views (of GOVERNANCE_VIEWS) the member wants to see if they 
							are a manager or owner.
		helpingRoles:		Helping roles the member has chosen (curator, guide, liaison).
		helpingRolesAvailable:	A manager/owner can ban a member from taking on these roles in future
							(this is for if people abuse them).
		guideIntro:			An introduction to be shown if the person is a guide
							about what sorts of questions they can best answer.
		
		nicknameIsRealName:	Whether their nickname is their real name. For display only.
		profileText:		Small amount of member-submitted info about themselves.
							Can include URLs which are converted to links.
		profileImage:		Thumbnail picture. Optional.
		
		lastEnteredArticle:	These "last" dates are for quickly showing activity.
		lastEnteredAnnotation: 	These "last" dates are for quickly showing activity.
		lastAnsweredQuestion:	These "last" dates are for quickly showing activity.
		lastReadAnything:	These "last" dates are for quickly showing activity.
		nudgePoints: 		Points accumulated by activity. Used for nudging articles.

	"""
	community = db.ReferenceProperty(Community, required=True, collection_name="members_to_community")
	nickname = db.StringProperty(default=NO_NICKNAME_SET)
	googleAccountID = db.StringProperty(required=True)
	googleAccountEmail = db.StringProperty(required=True)
	isOnlineMember = db.BooleanProperty(default=True)
	active = db.BooleanProperty(default=True)
	acceptsMessages = db.BooleanProperty(default=True)
	liaisonAccountID = db.StringProperty(default=None)
	
	timeZoneName = db.StringProperty()
	timeFormat = db.StringProperty()
	dateFormat = db.StringProperty()
	
	governanceType = db.StringProperty(choices=GOVERNANCE_ROLE_TYPES, default="member")
	governanceView = db.StringListProperty(default=None)
	helpingRoles = db.ListProperty(bool, default=[False, False, False])
	helpingRolesAvailable = db.ListProperty(bool, default=[True, True, True])
	guideIntro = db.TextProperty(default="")
	guideIntro_formatted = db.TextProperty()
	guideIntro_format = db.StringProperty(default="plain text")
	
	nicknameIsRealName = db.BooleanProperty(default=False)
	profileText = db.TextProperty(default="No profile information.")
	profileText_formatted = db.TextProperty()
	profileText_format = db.StringProperty(default="plain text")
	profileImage = db.BlobProperty(default=None)
	
	joined = TzDateTimeProperty(auto_now_add=True)
	lastEnteredArticle = db.DateTimeProperty()
	lastEnteredAnnotation = db.DateTimeProperty()
	lastEnteredLink = db.DateTimeProperty()
	lastAnsweredQuestion = db.DateTimeProperty()
	lastReadAnything = db.DateTimeProperty()
	nudgePoints = db.IntegerProperty(default=50)
	
	viewTimeEnd = TzDateTimeProperty(auto_now_add=True)
	viewTimeFrameInSeconds = db.IntegerProperty(default=3600)
	viewNumTimeFrames = db.IntegerProperty(default=1)
	viewNumTimeColumns = db.IntegerProperty(default=10)
	
	def initialize(self):
		self.timeZoneName = self.community.defaultTimeZoneName
		self.timeFormat = self.community.defaultTimeFormat
		self.dateFormat = self.community.defaultDateFormat
	
	def getViewingPreferences(self):
		return ViewingPreferences.all().filter("owner = ", self.key()).fetch(FETCH_NUMBER)
	
	def getViewStartTime(self):
		deltaSeconds = self.viewTimeFrameInSeconds * self.viewNumTimeFrames
		return self.viewTimeEnd - timedelta(seconds=deltaSeconds)
			
	def setViewTimeFrameFromTimeUnitString(self, unit):
		for aUnit in TIME_UNIT_STRINGS.keys():
			if unit == aUnit:
				self.viewTimeFrameInSeconds = TIME_UNIT_STRINGS[aUnit]
				break
				# caller should do the put
			
	def getUnitStringForViewTimeFrame(self):
		for key, value in TIME_UNIT_STRINGS.items():
			if self.viewTimeFrameInSeconds == value:
				return key
			
	def setTimeFrameToStartAtFirstPublish(self):
		deltaSeconds = self.viewTimeFrameInSeconds * self.viewNumTimeFrames
		self.viewTimeEnd = self.community.firstPublish + timedelta(seconds=deltaSeconds)
	
	def googleUserEmailOrNotOnline(self):
		if self.isOnlineMember:
			return self.googleAccountEmail
		return "Offline member"
	
	def isCurator(self):
		return self.helpingRoles[0]
	
	def isGuide(self):
		return self.helpingRoles[1]
	
	def isLiaison(self):
		return self.helpingRoles[2]
	
	def hasAnyHelpingRole(self):
		return self.helpingRoles[0] or self.helpingRoles[1] or self.helpingRoles[2]

	def canTakeOnAnyHelpingRole(self):
		return self.helpingRolesAvailable[0] or self.helpingRolesAvailable[1] or self.helpingRolesAvailable[2]
	
	def setGovernanceType(self, type):
		self.governanceType = type
		
	def isRegularMember(self):
		return self.governanceType == "member"
	
	def checkedIfRegularMember(self):
		if self.isRegularMember():
			return "checked"
		return ""
	
	def isManager(self):
		return self.governanceType == "manager"
	
	def isManagerOrOwner(self):
		return self.governanceType == "manager" or self.governanceType == "owner"
	
	def checkedIfManager(self):
		if self.isManager():
			return "checked"
		return ""
	
	def isOwner(self):
		return self.governanceType == "owner"
	
	def checkedIfOwner(self):
		if self.isOwner():
			return "checked"
		return ""
	
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
	
	def getNonDraftArticlesAttributedToMember(self):
		return Article.all().filter("creator = ", self.key()).filter("draft = ", False).filter("character = ", None).fetch(FETCH_NUMBER)
	
	def getDraftArticles(self):
		return Article.all().filter("creator = ", self.key()).filter("draft = ", True).fetch(FETCH_NUMBER)
	
	def getNonDraftAnnotationsAttributedToMember(self):
		return Annotation.all().filter("creator = ", self.key()).filter("draft = ", False).filter("character = ", None).fetch(FETCH_NUMBER)
	
	def getDraftAnswersForArticle(self, article):
		return Answer.all().filter("creator = ", self.key()).filter("draft = ", True).filter("referent = ", article.key()).fetch(FETCH_NUMBER)
	
	def getNonDraftAnswersAboutArticlesAttributedToMember(self):
		return Answer.all().filter("creator = ", self.key()).filter("draft = ", False).filter("character = ", None).filter("referentType = ", "article").fetch(FETCH_NUMBER)
	
	def getDraftAnnotations(self):
		return Annotation.all().filter("creator = ", self.key()).filter("draft = ", True).fetch(FETCH_NUMBER)
	
	def getArticlesWithDraftAnswers(self):
		answers = Answer.all().filter("creator = ", self.key()).filter("draft = ", True).filter("referentType = ", "article").fetch(FETCH_NUMBER)
		articles = {}
		for answer in answers:
			if not articles.has_key(answer.referent):
				articles[answer.referent] = 1
		return articles.keys()
	
class PendingMember(db.Model):
	""" A person who has been invited to join a community but who has not yet logged in.
		
	Properties
		community:			Which community they have been invited to join.
		email:				An email address related to a Google account.
		invited:			When invited.
	"""
	community = db.ReferenceProperty(Community, required=True, collection_name="pending_members_to_community")
	email = db.StringProperty(required=True)
	invited = TzDateTimeProperty(auto_now_add=True)
	
class Character(db.Model):
	""" Used to anonymize entries but provide some information about intent. Optional.
	
	Properties
		community:			The Rakontu community this character belongs to.
		name:				The fictional name of the character, like "Coyote".
		description:		Simple text description of the character.
		etiquetteStatement:	Just some guidelines for when the person is taking on the character.
							How not to behave.
		image:				Optional image.
	"""
	community = db.ReferenceProperty(Community, required=True, collection_name="characters_to_community")
	name = db.StringProperty(required=True)
	description = db.TextProperty(default="")
	description_formatted = db.TextProperty()
	description_format = db.StringProperty(default="plain text")
	etiquetteStatement = db.TextProperty(default="")
	etiquetteStatement_formatted = db.TextProperty()
	etiquetteStatement_format = db.StringProperty(default="plain text")
	image = db.BlobProperty(default=None)
	
# --------------------------------------------------------------------------------------------
# Answer
# --------------------------------------------------------------------------------------------

class Answer(db.Model):
	""" Answer to question. 
	
	Properties
		question: 			Refers to annotation question, for display.
		referent:			Whatever the answer refers to.
		referentType:		Whether the answer refers to an article or member.
		creator:			Who answered the question.
		
		answerIfBoolean:	True or false. Only used if question type is boolean.
		answerIfText:		String. Only used if question type is text.
		answerIfMultiple:	List of strings. Only used if question type is ordinal or nominal and multiple flag is set.
		answerIfValue:		Integer. Only used if question type is value.
							(Note we are leaving float values out.)
		
		created: 			When object was created.
		edited: 			When last changed.
		published:			When published (if).
		draft:				Whether this is a draft or published entry.
	"""
	question = db.ReferenceProperty(Question, collection_name="answers_to_questions")
	referent = db.ReferenceProperty(None, collection_name="answers_to_objects")
	referentType = db.StringProperty(default="article")
	creator = db.ReferenceProperty(Member, collection_name="answers_to_creators")
	community = db.ReferenceProperty(Community, collection_name="answers_to_community")
	
	collectedOffline = db.BooleanProperty(default=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="answers_to_liaisons")
	character = db.ReferenceProperty(Character, default=None)
	
	answerIfBoolean = db.BooleanProperty(default=False)
	answerIfText = db.StringProperty(default="")
	answerIfMultiple = db.StringListProperty(default=["", "", "", "", "", "", "", "", "", ""])
	answerIfValue = db.IntegerProperty(default=0)
	
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True)
	published = TzDateTimeProperty(auto_now_add=True)
	draft = db.BooleanProperty(default=True)
	articleNudgePointsWhenPublished = db.ListProperty(int, default=[0,0,0,0,0])
	articleActivityPointsWhenPublished = db.IntegerProperty(default=0)
	
	def questionKey(self):
		return self.question.key()
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else:
			return self.creator.nickname
		
	def publish(self):
		if self.referentType == "article":
			self.draft = False
			self.published = datetime.now(pytz.utc)
			self.put()
			self.referent.recordAction("added", self)
			if self.referentType == "article":
				for i in range(5):
					self.articleNudgePointsWhenPublished[i] = self.referent.nudgePoints[i]
				self.articleActivityPointsWhenPublished = self.referent.activityPoints
				self.put()
			self.creator.nudgePoints += self.community.getNudgePointsPerActivityForActivityName("answering question")
			self.creator.lastAnsweredQuestion = datetime.now(pytz.utc)
			self.creator.put()
			self.community.lastPublish = self.published
			self.community.put()
				
	def getImageLinkForType(self):
		return'<img src="/images/answers.png" alt="answer" border="0">'
	
	def displayStringShort(self):
		return self.displayString(includeQuestionName=False)
	
	def displayString(self, includeQuestionName=True):
		if includeQuestionName:
			result = self.question.name + ": "
		else: 
			result = ""
		if self.question.type == "boolean":
			if self.answerIfBoolean: 
				result += "yes"
			else:
				result += "no"
		elif self.question.type == "text":
			result += self.answerIfText
		elif self.question.type == "ordinal" or self.question.type == "nominal":
			answersToReport = []
			for answer in self.answerIfMultiple:
				if len(answer):
					answersToReport.append(answer)
			result +=  ", ".join(answersToReport)
		elif self.question.type == "value":
			result +=  "%s" % self.answerIfValue
		return result
	
	def linkString(self):
		return self.displayString()
		
# --------------------------------------------------------------------------------------------
# Article
# --------------------------------------------------------------------------------------------

class Article(db.Model):
	""" Main element of the system. 
	
	Properties
		title:				A name for the article. Appears in the interface.
		text:				Main body of content. What is read. 
		type:				Whether it is a story, pattern, collage, invitation or resource.

		creator: 			Member who contributed the story. May be online or offline.
		community:			The Rakontu community this article belongs to.
		collectedOffline:	Whether it was contributed by an offline member.
		liaison:			Person who entered the article for off-line member. None if not offline.
		character: 	Reference to fictional member name (from global list).
		
		instructionsIfPattern:	If this is a pattern, instructions on how to reproduce it.
		screenshotIfPattern:	If this is a pattern, an uploaded picture of it.

		tookPlace:			When the events the article is about took place.
		collected:			When article was collected, usually from an off-line member.
		created:			When article was added to database.
		edited:				When the text or title was last changed.
		published:			When the article was published.
		draft:				Whether this is a draft or published entry.
		
		lastRead:			When it was last accessed by anyone.
	"""
	title = db.StringProperty(required=True)
	text = db.TextProperty(default="No text")
	text_formatted = db.TextProperty()
	text_format = db.StringProperty(default="plain text")
	type = db.StringProperty(choices=ARTICLE_TYPES, required=True)

	creator = db.ReferenceProperty(Member, collection_name="articles")
	community = db.ReferenceProperty(Community, required=True, collection_name="articles_to_community")
	collectedOffline = db.BooleanProperty(default=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="articles_to_liaisons")
	character = db.ReferenceProperty(Character, default=None)
	
	tookPlace = TzDateTimeProperty(auto_now_add=True)
	collected = TzDateTimeProperty(default=None)
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True)
	published = TzDateTimeProperty(auto_now_add=True)
	draft = db.BooleanProperty(default=True)
	
	lastRead = TzDateTimeProperty(default=None)
	lastAnnotatedOrAnsweredOrLinked = TzDateTimeProperty(default=None)
	activityPoints = db.IntegerProperty(default=0)
	nudgePoints = db.ListProperty(int, default=[0,0,0,0,0])
	
	def getPublishDateForMember(self, member):
		if member:
			localTime = self.published.astimezone(timezone(member.timeZoneName))
			return localTime.strftime(str(member.timeFormat))
		else:
			return self.published
	
	def nudgePointsCombined(self):
		return self.nudgePoints[0] + self.nudgePoints[1] + self.nudgePoints[2] + self.nudgePoints[3] + self.nudgePoints[4]
	
	def attributedToMember(self):
		return self.character == None
	
	def isStory(self):
		return self.type == "story"
	
	def isResource(self):
		return self.type == "resource"
	
	def isInvitation(self):
		return self.type == "invitation"
	
	def isPatternOrCollage(self):
		return self.type == "pattern" or self.type == "collage"
	
	def isCollage(self):
		return self.type == "collage"
	
	def getAttachments(self):
		return Attachment.all().filter("article =", self.key()).fetch(FETCH_NUMBER)
	
	def getAnswers(self):
		return Answer.all().filter("referent = ", self.key()).fetch(FETCH_NUMBER)
	
	def getNonDraftAnswers(self):
		return Answer.all().filter("referent = ", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)

	def getNonDraftAnnotationsOfType(self, type):
		return Annotation.all().filter("article =", self.key()).filter("type = ", type).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getNonDraftAnnotations(self):
		return Annotation.all().filter("article =", self.key()).filter("draft = ", False).fetch(FETCH_NUMBER)
	
	def getAllLinks(self):
		result = []
		outgoingLinks = Link.all().filter("articleFrom =", self.key()).fetch(FETCH_NUMBER)
		incomingLinks = Link.all().filter("articleTo =", self.key()).fetch(FETCH_NUMBER)
		result.extend(outgoingLinks)
		result.extend(incomingLinks)
		return result
	
	def getLinksOfType(self, type):
		result = []
		outgoingLinks = self.getOutgoingLinksOfType(type)
		incomingLinks = self.getIncomingLinksOfType(type)
		result.extend(outgoingLinks)
		result.extend(incomingLinks)
		return result
	
	def getOutgoingLinksOfType(self, type):
		return Link.all().filter("articleFrom =", self.key()).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def getIncomingLinksOfType(self, type):
		return Link.all().filter("articleTo =", self.key()).filter("type = ", type).fetch(FETCH_NUMBER)
	
	def getIncomingLinksOfTypeFromType(self, type, fromType):
		result = []
		incomingLinks = self.getIncomingLinksOfType(type)
		for link in incomingLinks:
			if link.articleFrom.type == fromType:
				result.append(link)
		return result
	
	def getImageLinkForType(self):
		if self.type == "story":
			imageText = '<img src="/images/story.png" alt="story" border="0">'
		elif self.type == "pattern":
			imageText = '<img src="/images/pattern.png" alt="pattern" border="0">'
		elif self.type == "collage":
			imageText = '<img src="/images/collage.png" alt="collage" border="0">'
		elif self.type == "invitation":
			imageText = '<img src="/images/invitation.png" alt="invitation" border="0">'
		elif self.type == "resource":
			imageText = '<img src="/images/resource.png" alt="resource" border="0">'
		return imageText
	
	def getAnswersForMember(self, member):
		return Answer.all().filter("referent = ", self.key()).filter("creator = ", member.key()).fetch(FETCH_NUMBER)
	
	def getNudgesForMember(self, member):
		return Annotation.all().filter("article = ", self.key()).filter("type = ", "nudge").filter("creator = ", member.key()).fetch(FETCH_NUMBER)
	
	def getTotalNudgePointsForMember(self, member):
		nudges = self.getNudgesForMember(member)
		result = 0
		for nudge in nudges:
			result += nudge.totalNudgePointsAbsolute()
		return result
	
	def memberCanNudge(self, member):
		return member.key() != self.creator.key()
	
	def recordAction(self, action, referent):
		if referent.__class__.__name__ == "Article":
			referentType = referent.type
			if action == "read":
				self.lastRead = datetime.now(pytz.utc)
		elif referent.__class__.__name__ == "Annotation":
			referentType = referent.type
			self.lastAnnotatedOrAnsweredOrLinked = datetime.now(pytz.utc)
		elif referent.__class__.__name__ == "Answer":
			referentType = "answer"
			self.lastAnnotatedOrAnsweredOrLinked = datetime.now(pytz.utc)
		elif referent.__class__.__name__ == "Link":
			referentType = referent.type + " link"
			self.lastAnnotatedOrAnsweredOrLinked = datetime.now(pytz.utc)
		self.activityPoints += DEFAULT_ACTIVITY_ACCUMULATIONS[referentType]
		self.nudgePoints = self.getCurrentTotalNudgePointsInAllCategories()
		self.put()
				
	def getCurrentTotalNudgePointsInAllCategories(self):
		result = [0,0,0,0,0]
		for nudge in self.getNonDraftAnnotationsOfType("nudge"):
			i = 0
			for value in nudge.valuesIfNudge:
				result[i] += value
				i += 1
		return result
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else: 
			return self.creator.nickname

	def publish(self):
		self.draft = False
		self.published = datetime.now(pytz.utc)
		self.recordAction("added", self)
		self.put()
		self.creator.nudgePoints += self.community.getNudgePointsPerActivityForActivityName("telling")
		self.creator.lastEnteredArticle = datetime.now(pytz.utc)
		self.creator.put()
		for answer in self.getAnswersForMember(self.creator):
			answer.publish()
		self.community.lastPublish = self.published
		if not self.community.firstPublishSet:
			self.community.firstPublish = self.published
			self.community.firstPublishSet = True
		self.community.put()
		
	def shortFormattedText(self):
		if len(self.text_formatted) > 100:
			return "%s ..." % self.text_formatted[:98]
		else:
			return self.text_formatted

class Link(db.Model):
	""" For holding on to links between articles.
	
	Properties
		articleFrom:		Where the link originated. Story read first, or pattern/collage.
		articleTo:			Article referred to. Usually story.
		creator: 			Member who created the link. May be online or offline.
		type:				One of retold, reminded, related, included.
		comment:			Optional user comment about the linkage, written when link made.
		published:			When created/published (no draft links).
	"""
	articleFrom = db.ReferenceProperty(Article, collection_name="linksFrom", required=True)
	articleTo = db.ReferenceProperty(Article, collection_name="linksTo", required=True)
	creator = db.ReferenceProperty(Member, collection_name="links")
	published = TzDateTimeProperty(auto_now_add=True)
	type = db.StringProperty(choices=LINK_TYPES, required=True)
	comment = db.StringProperty(default="")
	articleNudgePointsWhenPublished = db.ListProperty(int, default=[0,0,0,0,0])
	articleActivityPointsWhenPublished = db.IntegerProperty(default=0)
	
	def publish(self):
		self.published = datetime.now(pytz.utc)
		self.put()
		self.articleFrom.recordAction("added", self)
		self.articleTo.recordAction("added", self)
		for i in range(5):
			self.articleNudgePointsWhenPublished[i] = self.articleFrom.nudgePoints[i]
		self.articleActivityPointsWhenPublished = self.articleFrom.activityPoints
		self.put()
		i = 0
		nudgePointType = None
		for verb in ACTIVITIES_VERB:
			if type == verb:
				nudgePointType = ACTIVITIES_GERUND[i]
				break
			i += 1
		if nudgePointType:
			self.creator.nudgePoints = self.community.getNudgePointsPerActivityForActivityName(nudgePointType)
		self.creator.lastEnteredLink = datetime.now(pytz.utc)
		self.creator.put()
		self.articleFrom.community.lastPublish = self.published
		if not self.articleFrom.community.firstPublishSet:
			self.articleFrom.community.firstPublish = self.published
			self.articleFrom.community.firstPublishSet = True
		self.articleFrom.community.put()
		
	def attributedToMember(self):
		return True
		
	def getImageLinkForType(self):
		return'<img src="/images/link.png" alt="link" border="0">'
	
	def displayString(self):
		result = '<a href="read?%s">%s</a> (%s' % (self.articleTo.key(), self.articleTo.title, self.type)
		if self.comment:
			result += ", %s)" % self.comment
		else:
			result += ")"
		return result
	
	def linkString(self):
		return self.displayString()
		
class Attachment(db.Model):
	""" For binary attachments to articles.
	
	Properties:
		name:				Name of the attachment.
		mimeType:			Determines how it is shown/downloaded.
		fileName:			The name of the file that was uploaded.
		data:				Binary data.
		article:			Which article it is associated with. (Only one allowed.)
	"""
	name = db.StringProperty()
	mimeType = db.StringProperty()
	fileName = db.StringProperty()
	data = db.BlobProperty()
	article = db.ReferenceProperty(Article, collection_name="attachments")
	
# --------------------------------------------------------------------------------------------
# Annotations
# --------------------------------------------------------------------------------------------

class Annotation(db.Model):
	""" Additions to articles.
	
	Properties
		article:			The thing being annotated.
		creator: 			Member who contributed the story. May be online or offline.
		community:			The Rakontu community this annotation belongs to.
							Maybe not necessary, but if you wanted to get a list of these without going through
							articles, this would be useful.
		type:				One of tag, comment, request or nudge.
		
		shortString:		A short string, usually used as a title
		longString:			A text property, used for the comment or request body.
		tagsIfTagSet:		A set of five tags, any or all of which might be blank.
		valuesIfNudge:		The number of nudge points (+ or -) this adds to the article.
							One value per category (up to 5).

		collectedOffline:	Whether it was contributed by an offline member.
		liaison:			Person who entered the article for off-line member. None if not offline.
		character: 	Reference to fictional member name (from global list).

		collected:			When article was collected, usually from an off-line member.
		created:			When article was added to database.
		edited:				When the text or title was last changed.
		published:			When the annotation was published.
		draft:				Whether this is a draft or published entry.
		
		inappropriateMarks:	A list of user comments marking the annotation as inappropriate.
	"""
	article = db.ReferenceProperty(Article, required=True, collection_name="annotations")
	creator = db.ReferenceProperty(Member, collection_name="annotations")
	community = db.ReferenceProperty(Community, required=True, collection_name="annotations_to_community")
	type = db.StringProperty(choices=ANNOTATION_TYPES, required=True)
	
	shortString = db.StringProperty()
	longString = db.TextProperty()
	longString_formatted = db.TextProperty()
	longString_format = db.StringProperty(default="plain text")
	tagsIfTagSet = db.StringListProperty(default=["", "", "", "", ""])
	valuesIfNudge = db.ListProperty(int, default=[0,0,0,0,0])

	collectedOffline = db.BooleanProperty(default=False)
	liaison = db.ReferenceProperty(Member, default=None, collection_name="annotations_liaisoned")
	character = db.ReferenceProperty(Character, default=None)

	collected = TzDateTimeProperty(default=None)
	created = TzDateTimeProperty(auto_now_add=True)
	edited = TzDateTimeProperty(auto_now_add=True)
	published = TzDateTimeProperty(auto_now_add=True)
	draft = db.BooleanProperty(default=True)
	articleNudgePointsWhenPublished = db.ListProperty(int, default=[0,0,0,0,0])
	articleActivityPointsWhenPublished = db.IntegerProperty(default=0)
	
	def isComment(self):
		return self.type == "comment"
	
	def isRequest(self):
		return self.type == "request"
	
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
	
	def attributedToMember(self):
		return self.character == None
	
	def memberNickNameOrCharacterName(self):
		if self.character:
			return self.character.name
		else:
			return self.creator.nickname
		
	def typeAsURL(self):
		if self.type != "tag set":
			return self.type
		return "tagset"
	
	def displayString(self):
		if self.type == "comment" or self.type == "request":
			return self.shortString
		elif self.type == "tag set":
			return ", ".join(self.tagsIfTagSet)
		elif self.type == "nudge":
			result = []
			for i in range(5):
				if self.valuesIfNudge[i] != 0:
					result.append("%s: %s" % (self.community.nudgeCategories[i], self.valuesIfNudge[i]))
			if self.shortString:
				result.append("(%s)" % self.shortString)
			return ", ".join(result)
	
	def linkString(self):
		if self.type == "comment" or self.type == "request":
			if self.longString_formatted and len(self.longString_formatted) > 30:
				return '<a href="readAnnotation?%s">%s</a>' % (self.key(), self.displayString())
			elif self.longString_formatted:
				return "%s: %s" % (self.shortString, self.longString_formatted)
			else:
				return self.shortString
		else:
			return self.displayString()
		
	def getImageLinkForType(self):
		if self.type == "comment":
			imageText = '<img src="/images/comments.png" alt="comment" border="0">'
		elif self.type == "request":
			imageText = '<img src="/images/requests.png" alt="request" border="0">'
		elif self.type == "tag set":
			imageText = '<img src="/images/tags.png" alt="tag set" border="0">'
		elif self.type == "nudge":
			imageText = '<img src="/images/nudges.png" alt="nudge" border="0">'
		return imageText
	
	def publish(self):
		self.draft = False
		self.published = datetime.now(pytz.utc)
		self.put()
		self.article.recordAction("added", self)
		for i in range(5):
			self.articleNudgePointsWhenPublished[i] = self.article.nudgePoints[i]
		self.articleActivityPointsWhenPublished = self.article.activityPoints
		self.put()
		if self.type == "tag set":
			activity = "tagging"
		elif self.type == "comment":
			activity = "commenting"
		elif self.type == "request":
			activity =  "requesting"
		elif self.type == "nudge":
			activity = "nudging"
		self.creator.nudgePoints += self.community.getNudgePointsPerActivityForActivityName(activity)
		self.creator.put()
		self.community.lastPublish = self.published
		self.community.put()
				
class InappropriateFlag(db.Model):
	""" Flags that say anything is inappropriate and should be removed.
		Can only be added by curators, managers or owners. 
		Items can only be removed by managers, owners, or their creators.
	
	Properties
		referent:			What object is recommended for removal: article, annotation or answer.
		creator:			Who recommended removing the object.
		comment:			An optional comment on why removal is recommended.
		entered:			When the flag was created.
	"""
	referent = db.ReferenceProperty(None, required=True)
	creator = db.ReferenceProperty(Member, collection_name="flags")
	comment = db.StringProperty(default="")
	entered = TzDateTimeProperty(auto_now_add=True)
	
# --------------------------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------------------------

class Query(db.Model):
	""" Choice to show subsets of items in main viewer.

	Properties (common to all types):
		owner:			Who this query belongs to.
		created:			When it was created.

		type:				One of free text, tags, answers, members, activities, links. 
		targets:			All searches return articles, annotations, or members (no combinations). 
	"""
	owner = db.ReferenceProperty(Member, required=True, collection_name="queries")
	created = TzDateTimeProperty(auto_now_add=True)

	type = db.StringProperty(choices=QUERY_TYPES, required=True)
	targets = db.StringListProperty(choices=QUERY_TARGETS, required=True)
	
	""" Free text search
	
	Properties:
		targets:			Articles or annotations, or specific types of either.
		text:				The text to search on. Can include boolean AND, OR, NOT.
	Usage: 
		Show [QUERY_TARGETS] with <text> 
	Examples: 
		Show [comments] with <hate OR love> 
		(with selection) Show [nudges] in the selection with <NOT ""> (meaning, with non-blank nudge comments)
	"""
	text = db.StringProperty()
	
	""" Tag search
	
	Properties:
		targets:			Articles or annotations, or specific types of either. 
		tags:				List of tags to search on. 1-n.
		combination:		Whether to search for all or any of the tags listed.
	Usage:
		Show [QUERY_TARGETS] in which [All, ANY] of <tags> appear 
	Examples: 
		Show [invitations] with [ANY OF] the tags <"need for project", "important">
		(with selection) Show [resources] in the selection with the tag <"planning"> 
	"""
	tags = db.StringListProperty()
	combination = db.StringProperty(choices=BOOLEAN_CHOICES, default="ANY")
	
	""" Answer search
	
	Properties:
		targets:			Articles or annotations, or specific types of either. 
		questionAnswers:	List of strings denoting question and one or more answers.
							Saved together and parsed. 1-n.
		combination:		Whether to search for all or any of the question-answer sets listed.
	Usage:
		Show [QUERY_TARGETS] in which {questions+answers} appear 
	Examples: 
		Show [stories] with [ALL OF] <How do you feel ~ includes ~ happy> and <What was the outcome ~ is ~ bad>
		(with selection) Show [articles] in the selection with <How damaging is this story ~ >= ~ 75>
	"""
	questionAnswers = db.StringListProperty()
	
	""" Member search
	
	Properties:
		memberType:			What sort of member to find. 
		activity:			What the member should have done. 
		timeFrame:			When the member should have done it. 
	Usage:
		Show [MEMBER_TYPES] who have [ACTIVITIES_VERB] in [RECENT_TIME_FRAMES]
	Examples: 
		Show [off-line members] who [commented] in [the last week]
		(with selection) Show [members] who [nudged] the selected story in [the last hour]
	"""
	memberType = db.StringProperty(choices=MEMBER_TYPES)
	activity = db.StringProperty(choices=ACTIVITIES_VERB)
	timeFrame = db.StringProperty(choices=RECENT_TIME_FRAMES)
	
	""" Activity search
	Properties:
		targets:			Articles or annotations, or specific types of either. 
		activity:			What the member should have done. 
		memberIDS:			Who should have done it. 1-n.
		combination:		Whether to search for all or any of the members listed.
		timeFrame:			When the member(s) should have done it. 
	Usage:
		Show [QUERY_TARGETS] in which [ACTIVITIES_VERB] were done by {members} in [RECENT_TIME_FRAMES]
	Examples:
		Show [stories] [retold] by {Joe OR Jim} in [the past 6 months]
		(with selection) Show which of the selected [articles] {I} have [nudged] [ever]
	"""
	memberIDs = db.StringListProperty()
	
	""" Link search
	Properties:
		articleType:		Articles (without annotations). 
		linkType:			Type of link. 
		typeLinkedTo:		What sort of article should have been linked to. 
		memberIDS:			Who should have done it. 1-n.
		timeFrame:			When the member(s) should have done it. 
	Usage:
		Show [ARTICLE_TYPES] {members} connected with [LINK_TYPES] to [ARTICLE_TYPES] in [RECENT_TIME_FRAMES]
	Examples:
		Show [resources] {I} have [related] to [stories] in [the past month]
		(with selection) Show [stories] [included] in the selected pattern by {anyone} [ever]
	"""
	articleType = db.StringProperty(choices=ARTICLE_TYPES)
	linkType = db.StringProperty(choices=LINK_TYPES)
	typeLinkedTo = db.StringProperty(choices=ARTICLE_TYPES)
	
# --------------------------------------------------------------------------------------------
# Preferences
# --------------------------------------------------------------------------------------------

class ViewingPreferences(db.Model):
	""" Preferences for the main viewer. Each user has these, and there is a community-wide set as well for defaulting.
	
	Properties
		owner:				The member these preferences belong to.
		communityIfCommon:	If these are common default options for the community, which community they are for.
		
		xTimeStep:			What time unit to show in grid columns (day, week, month, etc).
		xTimeStepMultiplier:How many days, weeks, etc to show in one column.
		xStart:				What time to show in the first column.
		xStop:				What time to show in the last column.
		
		yPointStep:			How many points in vertical space are covered by one grid row.
		yTop:				What point number to show in the top row.
		yBottom:			What point number to show in the bottom row.
		yArrangement:		How to arrange items on the Y axis. 1-n.
		verticalPoints:		A number for each type of placement denoting how many points (+ or -) an article moves
							each time something happens. For time the unit is one day; all other placements are events.
							
		deepFreeze:		A number of points below which articles are not displayed, no matter what yBottom users pick.
							Used mainly at the community level, though users could set a different level for themselves.
	"""
	owner = db.ReferenceProperty(Member, required=True, collection_name="viewing_preferences")
	communityIfCommon = db.ReferenceProperty(Community, required=True, collection_name="prefs_to_community")
	
	xTimeStep = db.StringProperty(choices=TIME_FRAMES, default="day")
	xTimeStepMultiplier = db.IntegerProperty(default=1)
	xStart = db.DateTimeProperty(default=datetime(2009, 5, 1))
	xStop = db.DateTimeProperty(default=datetime(2009, 6, 1))
	
	yPointStep = db.IntegerProperty(default=10)
	yTop = db.IntegerProperty(default=100)
	yBottom = db.IntegerProperty(default=0)
	yArrangement = db.StringListProperty(choices=ACTIVITIES_GERUND, default=["time", "reading", "nudging"])
	verticalPoints = db.ListProperty(int, default=DEFAULT_ACTIVITY_POINTS_PER_EVENT)
	
	deepFreeze = db.IntegerProperty(default=0)
	
