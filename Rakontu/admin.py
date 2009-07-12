# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

from utils import *

class CreateRakontuPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		user = users.get_current_user()
		if users.is_current_user_admin():
			template_values = GetStandardTemplateDictionaryAndAddMore({
							   'title': TITLES["CREATE_RAKONTU"],
							   'rakontu_types': RAKONTU_TYPES,
							   })
			path = os.path.join(os.path.dirname(__file__), FindTemplate('admin/create.html'))
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect(START)
			
	@RequireLogin 
	def post(self):
		user = users.get_current_user()
		if users.is_current_user_admin():
			ownerEmail = self.request.get('ownerEmail').strip()
			if ownerEmail:
				rakontu = Rakontu(
								key_name=KeyName("rakontu"), 
								url=htmlEscape(self.request.get('url')), 
								name=htmlEscape(self.request.get('name')))
				rakontu.initializeFormattedTexts()
				rakontu.type = self.request.get("type")
				rakontu.put()
				if rakontu.type != RAKONTU_TYPES[-1]:
					GenerateDefaultQuestionsForRakontu(rakontu, rakontu.type)
				GenerateDefaultCharactersForRakontu(rakontu)
				# add administrator to Rakontu
				member = Member(
					key_name=KeyName("member"), 
					googleAccountEmail=user.email(),
					googleAccountID=user.user_id(),
					active=True,
					rakontu=rakontu,
					governanceType="member",
					nickname = "administrator")
				member.initialize()
				member.put()
				# add new owner as pending member
				newPendingMember = PendingMember(
					key_name=KeyName("pendingmember"), 
					rakontu=rakontu, 
					email=ownerEmail,
					governanceType="owner")
				newPendingMember.put()
				CopyDefaultResourcesForNewRakontu(rakontu, member)
				if ownerEmail == user.email():
					self.redirect(BuildURL("dir_manage", "url_first"))
				else:
					self.redirect(BuildURL("dir_admin", "url_admin"))
		else:
			self.redirect(START)

class AdministerSitePage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		# this one method does not require a rakontu and member, since the admin has to look at multiple rakontus.
		if users.is_current_user_admin():
			numSampleQuestions = Question.all().filter("rakontu = ", None).count()
			numDefaultResources = Entry.all().filter("rakontu = ", None).filter("type = ", "resource").count()
			numHelps = Help.all().count()
			template_values = GetStandardTemplateDictionaryAndAddMore({
						   	   'title': TITLES["REVIEW_RAKONTUS"], 
							   'rakontus': Rakontu.all().fetch(FETCH_NUMBER), 
						   	   'num_sample_questions': numSampleQuestions,
						   	   'num_default_resources': numDefaultResources,
						   	   "num_helps": numHelps,
							   # here we do NOT give the current_member or rakontu
							   })
			path = os.path.join(os.path.dirname(__file__), FindTemplate('admin/admin.html'))
			self.response.out.write(template.render(path, template_values))
		else:
			self.redirect(START)
			
	@RequireLogin 
	def post(self):
		# this one method does not require a rakontu and member, since the admin has to look at multiple rakontus.
		if users.is_current_user_admin():
			rakontus = Rakontu.all().fetch(FETCH_NUMBER)
			for aRakontu in rakontus:
				if "toggleActiveState|%s" % aRakontu.key() in self.request.arguments():
					aRakontu.active = not aRakontu.active
					aRakontu.put()
					self.redirect(BuildURL("dir_admin", "url_admin"))
				elif "remove|%s" % aRakontu.key() in self.request.arguments():
					aRakontu.removeAllDependents()
					db.delete(aRakontu)
					self.redirect(BuildURL("dir_admin", "url_admin"))
				elif "export|%s" % aRakontu.key() in self.request.arguments():
					self.redirect(BuildURL("dir_manage", "url_export", "rakontu_id=%s" % aRakontu.key()))
		else:
			self.redirect(START)
			
class GenerateSampleQuestionsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		if users.is_current_user_admin():
			GenerateSampleQuestions()
			self.redirect(self.request.headers["Referer"])
		else:
			self.redirect(START)
				
class GenerateSystemResourcesPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		if users.is_current_user_admin():
			GenerateSystemResources()
			self.redirect(self.request.headers["Referer"])
		else:
			self.redirect(START)
				
class GenerateHelpsPage(webapp.RequestHandler):
	@RequireLogin 
	def get(self):
		if users.is_current_user_admin():
			GenerateHelps()
			self.redirect(self.request.headers["Referer"])
		else:
			self.redirect(START)
				
