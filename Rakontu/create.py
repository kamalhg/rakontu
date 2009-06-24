# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

from utils import *

							 
class CreateCommunityPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		user = users.get_current_user()
		template_values = GetStandardTemplateDictionaryAndAddMore({
						   'title': "Create community",
						   'title_extra': None,
						   })
		path = os.path.join(os.path.dirname(__file__), 'templates/createCommunity.html')
		self.response.out.write(template.render(path, template_values))
			
	@RequireLogin 
	def post(self):
		user = users.get_current_user()
		community = Community(name=htmlEscape(self.request.get('name')))
		community.put()
		member = Member(
			googleAccountID=user.user_id(),
			googleAccountEmail=user.email(),
			active=True,
			community=community,
			governanceType="owner",
			nickname = htmlEscape(self.request.get('nickname')))
		member.initialize()
		member.put()
		self.redirect('/')
		
class EnterEntryPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			if self.request.uri.find("retell") >= 0:
				type = "story"
				linkType = "retell"
				itemFromKey = self.request.query_string
				itemFrom = db.get(itemFromKey)
				entry = None
				entryTypeIndexForCharacters = STORY_ENTRY_TYPE_INDEX
				entryName = None
			elif self.request.uri.find("remind") >= 0:
				type = "story"
				linkType = "remind"
				itemFromKey = self.request.query_string
				itemFrom = db.get(itemFromKey)
				entry = None
				entryTypeIndexForCharacters = STORY_ENTRY_TYPE_INDEX
				entryName = None
			elif self.request.uri.find("respond") >= 0:
				type = "story"
				linkType = "respond"
				itemFromKey = self.request.query_string
				itemFrom = db.get(itemFromKey)
				entry = None
				entryTypeIndexForCharacters = STORY_ENTRY_TYPE_INDEX
				entryName = None
			else:
				linkType = ""
				itemFrom = None
				i = 0
				for aType in ENTRY_AND_ANNOTATION_TYPES:
					if self.request.uri.find(aType) >= 0:
						type = aType
						entryTypeIndexForCharacters = i
						break
					i += 1
				if not self.request.uri.find("?") >= 0:
					entry = None
					entryName = None
				else:
					entryKey = self.request.query_string
					entry = db.get(entryKey)
					entryName = entry.title
			if entry:
				answers = entry.getAnswers()
				attachments = entry.getAttachments()
			else:
				answers = None
				attachments = None
			if type == "collage":
				if entry:
					includedLinksOutgoing = entry.getOutgoingLinksOfType("included")
				else:
					includedLinksOutgoing = []
				entries = community.getNonDraftStoriesInAlphabeticalOrder()
				entriesThatCanBeIncluded = []
				for anEntry in entries:
					found = False
					for link in includedLinksOutgoing:
						if entry and link.itemTo.key() == anEntry.key():
							found = True
							break
					if not found:
						entriesThatCanBeIncluded.append(anEntry)
				if entriesThatCanBeIncluded:
					firstColumn = []
					secondColumn = []
					thirdColumn = []
					numEntries = len(entriesThatCanBeIncluded)
					for i in range(numEntries):
						if i < numEntries // 3:
							firstColumn.append(entriesThatCanBeIncluded[i])
						elif i < 2 * numEntries // 3:
							secondColumn.append(entriesThatCanBeIncluded[i])
						else:
							thirdColumn.append(entriesThatCanBeIncluded[i])
			else:
				entriesThatCanBeIncluded = None
				firstColumn = []
				secondColumn = []
				thirdColumn = []
				includedLinksOutgoing = None
			if type == "pattern":
				if entry:
					referencedLinksOutgoing = entry.getOutgoingLinksOfType("referenced")
				else:
					referencedLinksOutgoing = []
				searches = community.getNonPrivateSavedSearches()
				searchesThatCanBeIncluded = []
				for aSearch in searches:
					found = False
					for link in referencedLinksOutgoing:
						if entry and link.itemTo.key() == aSearch.key():
							found = True
							break
					if not found:
						searchesThatCanBeIncluded.append(aSearch)
			else:
				searchesThatCanBeIncluded = []
				referencedLinksOutgoing = []
			if entryName:
				pageTitleExtra = "- %s" % entryName
			else:
				pageTitleExtra = ""
			template_values = GetStandardTemplateDictionaryAndAddMore({
							   'title': type.capitalize(), 
						   	   'title_extra': pageTitleExtra, 
							   'current_member': member,
							   'community': community, 
							   'entry_type': type,
							   'entry': entry,
							   'attachments': attachments,
							   # used by common_attribution
							   'attribution_referent_type': type,
							   'attribution_referent': entry,
							   'offline_members': community.getActiveOfflineMembers(),
							   'character_allowed': community.allowCharacter[entryTypeIndexForCharacters],
							   # used by common_questions
							   'refer_type': type,
							   'questions': community.getActiveQuestionsOfType(type),
							   'answers': answers,
							   # for a retold or remined story
							   'link_type': linkType,
							   'link_item_from': itemFrom,
							   # for a collage
							    'collage_first_column': firstColumn, 
								'collage_second_column': secondColumn, 
								'collage_third_column': thirdColumn, 
								'num_collage_rows': max(len(firstColumn), max(len(secondColumn), len(thirdColumn))),							   
								'included_links_outgoing': includedLinksOutgoing,
								# for a pattern
								'referenced_links_outgoing': referencedLinksOutgoing,
							    'searches_that_can_be_added_to_pattern': searchesThatCanBeIncluded,
							   })
			path = os.path.join(os.path.dirname(__file__), 'templates/visit/entry.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect("/")
			
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			for aType in ENTRY_TYPES:
				for argument in self.request.arguments():
					if argument.find(aType) >= 0:
						type = aType
						break
			if not self.request.uri.find("?") >= 0:
				entry = None
			else:
				entryKey = self.request.query_string
				entry = db.get(entryKey)
			newEntry = False
			if not entry:
				entry=Entry(community=community, type=type, title=DEFAULT_UNTITLED_ENTRY_TITLE)
				newEntry = True
			preview = False
			if "save|%s" % type in self.request.arguments():
				entry.draft = True
				entry.edited = datetime.now(tz=pytz.utc)
			elif "preview|%s" % type in self.request.arguments():
				entry.draft = True
				preview = True
			elif "publish|%s" % type in self.request.arguments():
				entry.draft = False
				entry.inBatchEntryBuffer = False
				entry.published = datetime.now(tz=pytz.utc)
			if self.request.get("title"):
				entry.title = htmlEscape(self.request.get("title"))
			text = self.request.get("text")
			format = self.request.get("text_format").strip()
			entry.text = text
			entry.text_formatted = db.Text(InterpretEnteredText(text, format))
			entry.text_format = format
			entry.collectedOffline = self.request.get("collectedOffline") == "yes"
			if entry.collectedOffline and member.isLiaison():
				foundMember = False
				for aMember in community.getActiveOfflineMembers():
					if self.request.get("offlineSource") == str(aMember.key()):
						entry.creator = aMember
						foundMember = True
						break
				if not foundMember:
					self.redirect('/result?offlineMemberNotFound') 
					return
				entry.liaison = member
				entry.collected = parseDate(self.request.get("year"), self.request.get("month"), self.request.get("day"))
			else:
				entry.creator = member
			if entry.collectedOffline:
				attributionQueryString = "offlineAttribution"
			else:
				attributionQueryString = "attribution"
			if self.request.get(attributionQueryString) != "member":
				entry.character = Character.get(self.request.get(attributionQueryString))
			else:
				entry.character = None
			if type == "resource":
				entry.resourceForHelpPage = self.request.get("resourceForHelpPage") == "yes"
				entry.resourceForNewMemberPage = self.request.get("resourceForNewMemberPage") == "yes"
				entry.resourceForManagersAndOwnersOnly = self.request.get("resourceForManagersAndOwnersOnly") == "yes"
			entry.put()
			if not entry.draft:
				entry.publish()
			linkType = None
			if self.request.get("link_item_from"):
				itemFrom = db.get(self.request.get("link_item_from"))
				if itemFrom:
					if self.request.get("link_type") == "retell":
						linkType = "retold"
					elif self.request.get("link_type") == "remind":
						linkType = "reminded"
					elif self.request.get("link_type") == "respond":
						linkType = "responded"
					elif self.request.get("link_type") == "relate":
						linkType = "related"
					elif self.request.get("link_type") == "include":
						linkType = "included"
					elif self.request.get("link_type") == "reference":
						linkType = "referenced"
					link = Link(itemFrom=itemFrom, itemTo=entry, type=linkType, \
								creator=member, community=community, \
								comment=htmlEscape(self.request.get("link_comment")))
					link.put()
					link.publish()
			if entry.isCollage():
				linksToRemove = []
				for link in entry.getOutgoingLinksOfType("included"):
					link.comment = self.request.get("linkComment|%s" % link.key())
					link.put()
					if self.request.get("removeLink|%s" % link.key()) == "yes":
						linksToRemove.append(link)
				for link in linksToRemove:
					db.delete(link)
				for anEntry in community.getNonDraftEntriesOfType("story"):
					if self.request.get("addLink|%s" % anEntry.key()) == "yes":
						link = Link(itemFrom=entry, itemTo=anEntry, type="included", creator=member, community=community)
						link.put()
						if not entry.draft:
							link.publish()
			if entry.isPattern():
				linksToRemove = []
				for link in entry.getOutgoingLinksOfType("referenced"):
					link.comment = self.request.get("linkComment|%s" % link.key())
					link.put()
					if self.request.get("removeLink|%s" % link.key()) == "yes":
						linksToRemove.append(link)
				for link in linksToRemove:
					db.delete(link)
				for aSearch in community.getNonPrivateSavedSearches():
					if self.request.get("addLink|%s" % aSearch.key()) == "yes":
						link = Link(itemFrom=entry, itemTo=aSearch, type="referenced", creator=member, community=community)
						link.put()
						if not entry.draft:
							link.publish()
			questions = Question.all().filter("community = ", community).filter("refersTo = ", type).fetch(FETCH_NUMBER)
			for question in questions:
				foundAnswers = Answer.all().filter("question = ", question.key()).filter("referent =", entry.key()).filter("creator = ", member.key()).fetch(FETCH_NUMBER)
				if foundAnswers:
					answerToEdit = foundAnswers[0]
				else:
					answerToEdit = Answer(question=question, community=community, creator=member, referent=entry, referentType="entry")
					keepAnswer = False
					queryText = "%s" % question.key()
					if question.type == "text":
						keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
						if keepAnswer:
							answerToEdit.answerIfText = htmlEscape(self.request.get(queryText))
					elif question.type == "value":
						keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
						if keepAnswer:
							oldValue = answerToEdit.answerIfValue
							try:
								answerToEdit.answerIfValue = int(self.request.get(queryText))
							except:
								answerToEdit.answerIfValue = oldValue
					elif question.type == "boolean":
						keepAnswer = queryText in self.request.params.keys()
						if keepAnswer:
							answerToEdit.answerIfBoolean = self.request.get(queryText) == "yes"
					elif question.type == "nominal" or question.type == "ordinal":
						if question.multiple:
							answerToEdit.answerIfMultiple = []
							for choice in question.choices:
								if self.request.get("%s|%s" % (question.key(), choice)) == "yes":
									answerToEdit.answerIfMultiple.append(choice)
									keepAnswer = True
						else:
							keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
							if keepAnswer:
								answerToEdit.answerIfText = self.request.get(queryText)
					answerToEdit.creator = member
					answerToEdit.character = entry.character
					answerToEdit.draft = entry.draft
					answerToEdit.inBatchEntryBuffer = entry.inBatchEntryBuffer
					answerToEdit.collected = entry.collected
					if keepAnswer:
						answerToEdit.put()
						if not answerToEdit.draft:
							answerToEdit.publish()
			foundAttachments = Attachment.all().filter("entry = ", entry.key()).fetch(FETCH_NUMBER)
			attachmentsToRemove = []
			for attachment in foundAttachments:
				for name, value in self.request.params.items():
					if value == "removeAttachment|%s" % attachment.key():
						attachmentsToRemove.append(attachment)
			if attachmentsToRemove:
				for attachment in attachmentsToRemove:
					db.delete(attachment)
			foundAttachments = Attachment.all().filter("entry = ", entry.key()).fetch(FETCH_NUMBER)
			for i in range(3):
				for name, value in self.request.params.items():
					if name == "attachment%s" % i:
						if value != None and value != "":
							filename = value.filename
							if len(foundAttachments) > i:
								attachmentToEdit = foundAttachments[i]
							else:
								attachmentToEdit = Attachment(entry=entry)
							j = 0
							mimeType = None
							for type in ACCEPTED_ATTACHMENT_FILE_TYPES:
								if filename.find(".%s" % type) >= 0:
									mimeType = ACCEPTED_ATTACHMENT_MIME_TYPES[j]
								j += 1
							if mimeType:
								attachmentToEdit.mimeType = mimeType
								attachmentToEdit.fileName = filename
								attachmentToEdit.name = htmlEscape(self.request.get("attachmentName%s" % i))
								attachmentToEdit.data = db.Blob(str(self.request.get("attachment%s" % i)))
								attachmentToEdit.put()
			if preview:
				self.redirect("/visit/preview?%s" % entry.key())
			elif entry.draft:
				if entry.collectedOffline:
					if entry.inBatchEntryBuffer:
						self.redirect("/liaise/review")
					else: # not in batch entry buffer
						self.redirect("/visit/drafts?%s" % entry.creator.key())
				else: # not collected offline 
					self.redirect("/visit/drafts?%s" % member.key())
			else: # new entry
				#member.viewTimeEnd = entry.published + timedelta(seconds=1)
				#member.put()
				self.redirect("/visit/read?%s" % entry.key())
		else: # no community or member
			self.redirect("/")
			
class AnswerQuestionsAboutEntryPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			if self.request.query_string:
				entry = Entry.get(self.request.query_string)
			if entry:
				answers = entry.getAnswersForMember(member)
				if len(answers):
					answerRefForQuestions =  answers[0]
				else:
					answerRefForQuestions = None
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Answers for", 
						   	   	   'title_extra': entry.title, 
								   'current_member': member,
								   'community': community, 
								   'entry': entry,
							   	   'attribution_referent_type': "answer set",
							       'attribution_referent': answerRefForQuestions,
								   'refer_type': entry.type,
								   'questions': community.getActiveQuestionsOfType(entry.type),
								   'answers': answers,
								   'community_members': community.getActiveMembers(),
								   'offline_members': community.getOfflineMembers(),
								   'character_allowed': community.allowCharacter[ANSWERS_ENTRY_TYPE_INDEX],
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/visit/answers.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect("/visit/look")
		else:
			self.redirect("/")
				
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entryKey = self.request.query_string
			entry = db.get(entryKey)
			if entry:
				newAnswers = False
				preview = False
				setAsDraft = False
				if "save" in self.request.arguments():
					setAsDraft = True
				elif "preview" in self.request.arguments():
					setAsDraft = True
					preview = True
				elif "publish" in self.request.arguments():
					setAsDraft = False
				collectedOffline = self.request.get("collectedOffline") == "yes"
				if collectedOffline and member.isLiaison():
					foundMember = False
					for aMember in community.getActiveOfflineMembers():
						if self.request.get("offlineSource") == str(aMember.key()):
							answersAlreadyInPlace = aMember.getDraftAnswersForEntry(entry)
							if answersAlreadyInPlace:
								self.redirect('/result?offlineMemberAlreadyAnsweredQuestions') 
								return
							creator = aMember
							foundMember = True
							break
					if not foundMember:
						self.redirect('/result?offlineMemberNotFound') 
						return
					liaison = member
					collected = parseDate(self.request.get("year"), self.request.get("month"), self.request.get("day"))
				else:
					creator = member
				if collectedOffline:
					attributionQueryString = "offlineAttribution"
				else:
					attributionQueryString = "attribution"
				character = None
				if self.request.get(attributionQueryString) != "member":
					characterKey = self.request.get(attributionQueryString)
					character = Character.get(characterKey)
				questions = Question.all().filter("community = ", community).filter("refersTo = ", entry.type).fetch(FETCH_NUMBER)
				for question in questions:
					foundAnswers = Answer.all().filter("question = ", question.key()).filter("referent =", entry.key()).filter("creator = ", member.key()).fetch(FETCH_NUMBER)
					if foundAnswers:
						answerToEdit = foundAnswers[0]
					else:
						answerToEdit = Answer(question=question, community=community, referent=entry, referentType="entry")
						newAnswers = True
					answerToEdit.creator = creator
					if collectedOffline:
						answerToEdit.liaison = liaison
						answerToEdit.collected = collected
					answerToEdit.character = character
					keepAnswer = False
					queryText = "%s" % question.key()
					if question.type == "text":
						keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
						if keepAnswer:
							answerToEdit.answerIfText = htmlEscape(self.request.get(queryText))
					elif question.type == "value":
						keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
						if keepAnswer:
							oldValue = answerToEdit.answerIfValue
							try:
								answerToEdit.answerIfValue = int(self.request.get(queryText))
							except:
								answerToEdit.answerIfValue = oldValue
					elif question.type == "boolean":
						keepAnswer = queryText in self.request.params.keys()
						if keepAnswer:
							answerToEdit.answerIfBoolean = self.request.get(queryText) == "yes"
					elif question.type == "nominal" or question.type == "ordinal":
						if question.multiple:
							answerToEdit.answerIfMultiple = []
							for choice in question.choices:
								if self.request.get("%s|%s" % (question.key(), choice)) == "yes":
									answerToEdit.answerIfMultiple.append(choice)
									keepAnswer = True
						else:
							keepAnswer = len(self.request.get(queryText)) > 0 and self.request.get(queryText) != "None"
							if keepAnswer:
								answerToEdit.answerIfText = self.request.get(queryText)
					answerToEdit.draft = setAsDraft
					if keepAnswer:
						if setAsDraft:
							answerToEdit.edited = datetime.now(tz=pytz.utc)
							answerToEdit.put()
						else:
							answerToEdit.publish()
				if preview:
					self.redirect("/visit/previewAnswers?%s" % entry.key())
				elif setAsDraft:
					self.redirect("/visit/drafts?%s" % creator.key()) 
				else:
					self.redirect("/visit/read?%s" % entry.key()) 
			else:
				self.redirect("/visit/read?%s" % entry.key())
		else:
			self.redirect("/")
			
class PreviewAnswersPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			if self.request.query_string:
				entry = Entry.get(self.request.query_string)
				answers = entry.getAnswersForMember(member)
			if entry and answers:
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Preview of", 
						   	   	   'title_extra': "Answers for %s " % entry.title, 
								   'current_member': member,
								   'community': community, 
								   'entry': entry,
								   'community_has_questions_for_this_entry_type': len(community.getActiveQuestionsOfType(entry.type)) > 0,
								   'questions': community.getActiveQuestionsOfType(entry.type),
								   'answers': answers,
								   })
			path = os.path.join(os.path.dirname(__file__), 'templates/visit/previewAnswers.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect("/")
		
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			if self.request.query_string:
				entry = Entry.get(self.request.query_string)
				if entry:
					if "edit" in self.request.arguments():
						self.redirect("/visit/answers?%s" % entry.key())
					elif "profile" in self.request.arguments():
						self.redirect("/visit/profile?%s" % member.key())
					elif "publish" in self.request.arguments():
						answers = entry.getAnswersForMember(member)
						for answer in answers:
							answer.draft = False
							answer.published = datetime.now(tz=pytz.utc)
							answer.put()
						self.redirect("/visit/look")

class EnterAnnotationPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			i = 0
			for aType in ANNOTATION_TYPES_URLS:
				if self.request.uri.find(aType) >= 0:
					type = ANNOTATION_TYPES[i]
					break
				i += 1
			i = 0
			for aType in ENTRY_AND_ANNOTATION_TYPES_URLS:
				if self.request.uri.find(aType) >= 0:
					entryTypeIndex = i
					break
				i += 1
			entry = None
			annotation = None
			if self.request.query_string:
				try:
					entry = Entry.get(self.request.query_string)
				except:
					annotation = Annotation.get(self.request.query_string)
					entry = annotation.entry
			if entry:
				if not entry.memberCanNudge(member):
					nudgePointsMemberCanAssign = 0
				else:
					nudgePointsMemberCanAssign = max(0, community.maxNudgePointsPerEntry - entry.getTotalNudgePointsForMember(member))
			else:
				nudgePointsMemberCanAssign = community.maxNudgePointsPerEntry
			if entry:
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "%s for" % type.capitalize(), 
						   	   	   'title_extra': entry.title, 
								   'current_member': member,
								   'community': community, 
								   'annotation_type': type,
								   'annotation': annotation,
							   	   'attribution_referent_type': type,
							       'attribution_referent': annotation,
								   'community_members': community.getActiveMembers(),
								   'offline_members': community.getOfflineMembers(),
								   'entry': entry,
								   'nudge_categories': community.nudgeCategories,
								   'nudge_points_member_can_assign': nudgePointsMemberCanAssign,
								   'character_allowed': community.allowCharacter[entryTypeIndex],
								   'included_links_outgoing': entry.getOutgoingLinksOfType("included"),
								   'already_there_tags': community.getNonDraftTags(),
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/visit/annotation.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect("/visit/look")
		else:
			self.redirect("/")
			
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			for aType in ANNOTATION_TYPES:
				for argument in self.request.arguments():
					if argument.find(aType) >= 0:
						type = aType
						break
			entry = None
			annotation = None
			newAnnotation = False
			if self.request.query_string:
				try:
					entry = Entry.get(self.request.query_string)
				except:
					annotation = Annotation.get(self.request.query_string)
					entry = annotation.entry
			if entry:
				if not annotation:
					annotation = Annotation(community=community, type=type, entry=entry)
					newAnnotation = True
				preview = False
				if "save|%s" % type in self.request.arguments():
					annotation.draft = True
					annotation.edited = datetime.now(tz=pytz.utc)
				elif "preview|%s" % type in self.request.arguments():
					annotation.draft = True
					preview = True
				elif "publish|%s" % type in self.request.arguments():
					annotation.draft = False
					annotation.inBatchEntryBuffer = False
					annotation.published = datetime.now(tz=pytz.utc)
				annotation.collectedOffline = self.request.get("collectedOffline") == "yes"
				if annotation.collectedOffline and member.isLiaison():
					foundMember = False
					for aMember in community.getActiveOfflineMembers():
						if self.request.get("offlineSource") == str(aMember.key()):
							annotation.creator = aMember
							foundMember = True
							break
					if not foundMember:
						self.redirect('/result?offlineMemberNotFound') 
						return
					annotation.liaison = member
					annotation.collected = parseDate(self.request.get("year"), self.request.get("month"), self.request.get("day"))
				else:
					annotation.creator = member
				if annotation.collectedOffline:
					attributionQueryString = "offlineAttribution"
				else:
					attributionQueryString = "attribution"
				if self.request.get(attributionQueryString) != "member":
					characterKey = self.request.get(attributionQueryString)
					character = Character.get(characterKey)
					annotation.character = character
				else:
					annotation.character = None
				if type == "tag set":
					annotation.tagsIfTagSet = []
					for i in range (NUM_TAGS_IN_TAG_SET):
						if self.request.get("tag%s" % i):
							annotation.tagsIfTagSet.append(htmlEscape(self.request.get("tag%s" % i)))
						elif self.request.get("alreadyThereTag%i" %i) and self.request.get("alreadyThereTag%i" %i) != "none":
							annotation.tagsIfTagSet.append(htmlEscape(self.request.get("alreadyThereTag%s" % i)))
				elif type == "comment":
					annotation.shortString = htmlEscape(self.request.get("shortString", default_value="No subject"))
					text = self.request.get("longString")
					format = self.request.get("longString_format").strip()
					annotation.longString = text
					annotation.longString_formatted = db.Text(InterpretEnteredText(text, format))
					annotation.longString_format = format
				elif type == "request":
					annotation.shortString = htmlEscape(self.request.get("shortString", default_value="No subject"))
					text = self.request.get("longString")
					format = self.request.get("longString_format").strip()
					annotation.longString = text
					annotation.longString_formatted = db.Text(InterpretEnteredText(text, format))
					annotation.longString_format = format
					if self.request.get("typeIfRequest") in REQUEST_TYPES:
						annotation.typeIfRequest = self.request.get("typeIfRequest")
					else:
						annotation.typeIfRequest = REQUEST_TYPES[len(REQUEST_TYPES) - 1]
				elif type == "nudge":
					oldTotalNudgePointsInThisNudge = annotation.totalNudgePointsAbsolute()
					nudgeValuesTheyWantToSet = []
					totalNudgeValuesTheyWantToSet = 0
					for i in range(NUM_NUDGE_CATEGORIES):
						category = community.nudgeCategories[i]
						if category:
							oldValue = annotation.valuesIfNudge[i]
							try:
								nudgeValuesTheyWantToSet.append(int(self.request.get("nudge%s" % i)))
							except:
								nudgeValuesTheyWantToSet.append(oldValue)
							totalNudgeValuesTheyWantToSet += abs(nudgeValuesTheyWantToSet[i])
					adjustedValues = []
					maximumAllowedInThisInstance = min(member.nudgePoints, community.maxNudgePointsPerEntry)
					if totalNudgeValuesTheyWantToSet > maximumAllowedInThisInstance:
						totalNudgePointsAllocated = 0
						for i in range(NUM_NUDGE_CATEGORIES):
							category = community.nudgeCategories[i]
							if category:
								overLimit = totalNudgePointsAllocated + nudgeValuesTheyWantToSet[i] > maximumAllowedInThisInstance
								if not overLimit:
									adjustedValues.append(nudgeValuesTheyWantToSet[i])
									totalNudgePointsAllocated += abs(nudgeValuesTheyWantToSet[i])
								else:
									break
					else:
						adjustedValues.extend(nudgeValuesTheyWantToSet)
					annotation.valuesIfNudge = [0,0,0,0,0]
					i = 0
					for value in adjustedValues:
						annotation.valuesIfNudge[i] = value
						i += 1
					annotation.shortString = htmlEscape(self.request.get("shortString"))
					newTotalNudgePointsInThisNudge = annotation.totalNudgePointsAbsolute()
					member.nudgePoints += oldTotalNudgePointsInThisNudge
					member.nudgePoints -= newTotalNudgePointsInThisNudge
					member.put()
				annotation.put()
				if not annotation.draft:
					annotation.publish()
				if preview:
					self.redirect("/visit/preview?%s" % annotation.key())
				elif annotation.draft:
					if annotation.collectedOffline:
						if entry.inBatchEntryBuffer:
							self.redirect("/liaise/review")
						else: # not in batch entry 
							self.redirect("/visit/drafts?%s" % annotation.creator.key()) 
					else: # not collected offline
						self.redirect("/visit/drafts?%s" % member.key())
				else: # not draft
					self.redirect("/visit/read?%s" % entry.key())
			else: # new entry
				self.redirect("/visit/look")
		else: # no community or member
			self.redirect("/")
			
class PreviewPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			annotation = None
			if self.request.query_string:
				try:
					entry = Entry.get(self.request.query_string)
				except:
					annotation = Annotation.get(self.request.query_string)
					entry = annotation.entry
			if entry:
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Preview", 
						   	   	   'title_extra': entry.title, 
								   'current_member': member,
								   'community': community, 
								   'annotation': annotation,
								   'entry': entry,
								   'included_links_outgoing': entry.getOutgoingLinksOfType("included"),
								   'community_has_questions_for_this_entry_type': len(community.getActiveQuestionsOfType(entry.type)) > 0,
								   'questions': community.getActiveQuestionsOfType(entry.type),
								   'answers_with_entry': entry.getAnswersForMember(member),
								   'nudge_categories': community.nudgeCategories,
								   })
			path = os.path.join(os.path.dirname(__file__), 'templates/visit/preview.html')
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect("/")
		
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			annotation = None
			if self.request.query_string:
				try:
					entry = Entry.get(self.request.query_string)
				except:
					annotation = Annotation.get(self.request.query_string)
					entry = annotation.entry
			if "batch" in self.request.arguments():
				if member.isLiaison():
					self.redirect('/liaise/review')
				else:
					self.redirect("/visit/look")
			elif "profile" in self.request.arguments():
				self.redirect("/visit/profile?%s" % member.key())
			elif annotation:
				if "edit" in self.request.arguments():
					self.redirect("/visit/%s?%s" % (annotation.typeAsURL(), annotation.key()))
				elif "publish" in self.request.arguments():
					annotation.publish()
					self.redirect("/visit/look?%s" % annotation.entry.key())
			else:
				if "edit" in self.request.arguments():
					self.redirect("/visit/%s?%s" % (entry.type, entry.key()))
				elif "publish" in self.request.arguments():
					entry.publish()
					self.redirect("/visit/look")
		else:
			self.redirect("/")
					
class RelateEntryPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
			entry = None
			if self.request.query_string:
				try:
					entry = Entry.get(self.request.query_string)
				except:
					entry = None
			if entry:
				links = entry.getLinksOfType("related")
				entries = community.getNonDraftEntriesInAlphabeticalOrder()
				entriesThatCanBeRelated = []
				for anEntry in entries:
					found = False
					for link in links:
						if link.itemTo.key() == anEntry.key() or link.itemFrom.key() == anEntry.key():
							found = True
					if not found and anEntry.key() != entry.key():
						entriesThatCanBeRelated.append(anEntry)
				if entriesThatCanBeRelated:
					firstColumn = []
					secondColumn = []
					thirdColumn = []
					numEntries = len(entriesThatCanBeRelated)
					for i in range(numEntries):
						if i < numEntries // 3:
							firstColumn.append(entriesThatCanBeRelated[i])
						elif i < 2 * numEntries // 3:
							secondColumn.append(entriesThatCanBeRelated[i])
						else:
							thirdColumn.append(entriesThatCanBeRelated[i])
					template_values = GetStandardTemplateDictionaryAndAddMore({
									'title': "Relate entries to",
								   	'title_extra': entry.title,
									'community': community, 
									'current_member': member, 
									'entry': entry,
									'entries_first_column': firstColumn, 
									'entries_second_column': secondColumn, 
									'entries_third_column': thirdColumn, 
									'num_rows': max(len(firstColumn), max(len(secondColumn), len(thirdColumn))),
									'related_links': links,
									})
					path = os.path.join(os.path.dirname(__file__), 'templates/visit/relate.html')
					self.response.out.write(template.render(path, template_values))
				else:
					self.redirect("read?%s" % entry.key()) # should not have link in this case CFK FIX
			else:
				self.redirect('/')
					
	@RequireLogin 
	def post(self):
		community, member, access = GetCurrentCommunityAndMemberFromSession()
		if access:
				entry = None
				if self.request.query_string:
					try:
						entry = Entry.get(self.request.query_string)
					except:
						entry = None
				if entry:
					linksToRemove = []
					for link in entry.getLinksOfType("related"):
						if self.request.get("linkComment|%s" % link.key()):
							link.comment = self.request.get("linkComment|%s" % link.key())
							link.put()
						if self.request.get("removeLink|%s" % link.key()) == "yes":
							linksToRemove.append(link)
					for link in linksToRemove:
						db.delete(link)
					for anEntry in community.getNonDraftEntries():
						if self.request.get("addLink|%s" % anEntry.key()) == "yes":
							link = Link(itemFrom=entry, itemTo=anEntry, type="related", \
										creator=member, community=community,
										comment=htmlEscape(self.request.get("linkComment|%s" % anEntry.key())))
							link.put()
							link.publish()
					self.redirect("read?%s" % entry.key())
				else:
					self.redirect("/visit/look")
		else:
			self.redirect("/")
			