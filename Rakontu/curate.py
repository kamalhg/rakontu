# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

from utils import *

class FlagOrUnflagItemPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			item = None
			if self.request.query_string:
				try:
					item = db.get(self.request.query_string)
				except:
					item = None
			if item:
				item.flaggedForRemoval = not item.flaggedForRemoval
				item.put()
				self.redirect(self.request.headers["Referer"])
			else:
				self.redirect("/visit/home")
		else:
			self.redirect("/")
	
class CurateFlagsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCuratorOrManagerOrOwner():
				(entries, annotations, answers, links, searches) = rakontu.getAllFlaggedItems()
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Review flags", 
						   	   	   'title_extra': None, 
						   	   	   'rakontu': rakontu, 
						   	   	   'current_member': member,
								   'entries': entries,
								   'annotations': annotations,
								   'answers': answers,
								   'links': links,
								   'searches': searches,
								   'search_locations': SEARCH_LOCATIONS,
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/curate/flags.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/visit/home')
		else:
			self.redirect("/")
				
	@RequireLogin 
	def post(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if "cancel" in self.request.arguments():
				self.redirect("/visit/home")
				return
			items = rakontu.getAllFlaggedItemsAsOneList()
			for item in items:
				if self.request.get("flagComment|%s" % item.key()):
					item.flagComment = self.request.get("flagComment|%s" % item.key())
					item.put()
				if self.request.get("unflag|%s" % item.key()) == "yes":
				 	item.flaggedForRemoval = False
				 	item.put()
			if member.isManagerOrOwner():
				for item in items:
					if self.request.get("removeComment|%s" % item.key()) == "yes":
						if item.__class__.__name__ == "Annotation": # nudge
							item.shortString = ""
						elif item.__class__.__name__ == "Link":
							item.comment = ""
						item.put()
					elif self.request.get("remove|%s" % item.key()) == "yes":
						if item.__class__.__name__ == "Entry":
							item.removeAllDependents()
						elif item.__class__.__name__ == "SavedSearch":
							item.deleteAllDependents()
						db.delete(item)
				self.redirect('/result?changessaved')
			elif member.isCurator():
				itemsToSendMessageAbout = []
				for item in items:
					if self.request.get("notify|%s" % item.key()) == "yes":
						itemsToSendMessageAbout.append(item)
				if itemsToSendMessageAbout:
					subject = "Reminder about flagged items from %s" % member.nickname
					URL = self.request.headers["Host"]
					messageLines = []
					messageLines.append("The curator %s wanted you to know that these items require your attention.\n" % member.nickname)
					itemsToSendMessageAbout.reverse()
					for item in itemsToSendMessageAbout:
						if item.__class__.__name__ == "Entry":
							linkKey = item.key()
							displayString = 'A %s called "%s"' % (item.type, item.title)
						elif item.__class__.__name__ == "Annotation":
							linkKey = item.entry.key()
							if item.shortString:
								shortString = " (%s)" % item.shortString
							else:
								shortString = ""
							displayString = 'A %s%s for the %s called "%s"' % (item.type, shortString, item.entry.type, item.entry.title)
 						elif item.__class__.__name__ == "Answer":
							linkKey = item.referent.key()
							displayString = 'An answer (%s) for the %s called "%s"' % (item.displayString(), item.referent.type, item.referent.title)
						elif item.__class__.__name__ == "Link":
							linkKey = item.itemFrom.key()
							if item.comment:
								commentString = " (%s)" % item.comment
							else:
								commentString = ""
							displayString = 'A link%s from the %s called "%s" to the %s called "%s"' % \
								(commentString, item.itemFrom.type, item.itemFrom.displayString(), item.itemTo.type, item.itemTo.displayString())
						elif item.__class__.__name__ == "SavedSearch":
							linkKey = item.key()
							displayString = item.name
						if item.__class__.__name__ == "SavedSearch":
							messageLines.append('* %s\n\n	http://%s/visit/home?%s (%s)\n' % (displayString, URL, linkKey, item.flagComment))
						else:
							messageLines.append('* %s\n\n	http://%s/visit/curate?%s (%s)\n' % (displayString, URL, linkKey, item.flagComment))
					messageLines.append("Thank you for your attention.\n")
					messageLines.append("Sincerely,")
					messageLines.append("	Your Rakontu site")
					message = "\n".join(messageLines)
					ownersAndManagers = rakontu.getManagersAndOwners()
					for ownerOrManager in ownersAndManagers:
						messageLines.insert(0, "Dear manager %s:\n" % ownerOrManager.nickname)
						messageBody = "\n".join(messageLines)
						message = mail.EmailMessage()
						message.sender = rakontu.contactEmail
						message.subject = subject
						message.to = ownerOrManager.googleAccountEmail
						message.body = messageBody
						DebugPrint(messageBody)
						# CFK FIX
						# not putting this last line in until I can start testing it, either locally or on the real server
						#message.send()
					self.redirect('/result?messagesent')
			else:
				self.redirect("/visit/home")
		else:
			self.redirect("/")
			
class CurateGapsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCurator():
				sortBy = self.request.query_string
				if not sortBy:
					sortBy = "activity"
				(entriesWithoutTags, \
				entriesWithoutLinks, \
				entriesWithoutAnswers, \
				entriesWithoutComments, \
				invitationsWithoutResponses,
				collagesWithoutInclusions) = rakontu.getNonDraftEntriesWithMissingMetadata(sortBy)
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Review gaps", 
						   	   	   'title_extra': None, 
								   'rakontu': rakontu, 
								   'sort_by': sortBy,
								   'entries_without_tags': entriesWithoutTags,
								   'entries_without_links': entriesWithoutLinks,
								   'entries_without_answers': entriesWithoutAnswers,
								   'entries_without_comments': entriesWithoutComments,
								   'invitations_without_responses': invitationsWithoutResponses,
								   'collages_without_inclusions': collagesWithoutInclusions,
								   'current_member': member,
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/curate/gaps.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/visit/home')
		else:
			self.redirect("/")
			
	@RequireLogin 
	def post(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCurator():
				if "sortBy" in self.request.arguments():
					self.redirect("/curate/gaps?%s" % self.request.get("sortBy"))
			else:
				self.redirect('/visit/home')
		else:
			self.redirect("/")
			
class CurateAttachmentsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCurator():
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Review attachments", 
						   	   	   'title_extra': None, 
								   'rakontu': rakontu, 
								   'attachments': rakontu.getAttachmentsForAllNonDraftEntries(),
								   'current_member': member,
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/curate/attachments.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/visit/home')
		else:
			self.redirect("/")
			
class CurateTagsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCurator():
				template_values = GetStandardTemplateDictionaryAndAddMore({
							   	   'title': "Review tags", 
						   	   	   'title_extra': None, 
								   'rakontu': rakontu, 
								   'tag_sets': rakontu.getNonDraftTagSets(),
								   'current_member': member,
								   })
				path = os.path.join(os.path.dirname(__file__), 'templates/curate/tags.html')
				self.response.out.write(template.render(path, template_values))
			else:
				self.redirect('/visit/home')
		else:
			self.redirect("/")
			
	@RequireLogin 
	def post(self):
		rakontu, member, access = GetCurrentRakontuAndMemberFromSession()
		if access:
			if member.isCurator():
				tagsets = rakontu.getNonDraftTagSets()
				for tagset in tagsets:
					tagset.tagsIfTagSet = []
					for i in range(NUM_TAGS_IN_TAG_SET):
						if self.request.get("tag%s|%s" % (i, tagset.key())):
							tagset.tagsIfTagSet.append(self.request.get("tag%s|%s" % (i, tagset.key())))
						else:
							tagset.tagsIfTagSet.append("")
				db.put(tagsets)
				self.redirect('/curate/tags')
