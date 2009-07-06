# --------------------------------------------------------------------------------------------
# RAKONTU
# Description: Rakontu is open source story sharing software.
# Version: pre-0.1
# License: GPL 3.0
# Google Code Project: http://code.google.com/p/rakontu/
# --------------------------------------------------------------------------------------------

import os
import string
import cgi
import htmllib

from models import *

import sys
sys.path.append("/Users/cfkurtz/Documents/personal/eclipse_workspace_kfsoft/Rakontu/lib/") 
from appengine_utilities.sessions import Session

from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from google.appengine.api import mail

webapp.template.register_template_library('djangoTemplateExtras')
import csv
import pytz

# ============================================================================================
# ============================================================================================
# PREPARING INFO FOR TEMPLATES
# ============================================================================================
# ============================================================================================

def RequireLogin(func):
	def check_login(request):
		if not users.get_current_user():
			loginURL = users.create_login_url("/")
			request.redirect(loginURL)
			return
		func(request)
	return check_login 

def GetCurrentRakontuAndMemberFromSession():
	session = Session()
	if session and session.has_key('rakontu_key'):
		rakontu_key = session['rakontu_key']
	else:
		rakontu_key = None
	if session and session.has_key('member_key'):
		member_key = session['member_key']
	else:
		member_key = None
	if rakontu_key: 
		rakontu = db.get(rakontu_key) 
	else:
		rakontu = None
	if member_key:
		member = db.get(member_key)
		if not member.rakontu.key() == rakontu.key():
			member = None
	else:
		member = None
	okayToAccess = rakontu and rakontu.active and member and member.active
	return rakontu, member, okayToAccess

def GetStandardTemplateDictionaryAndAddMore(newItems):
	items = {
		# constants
	   'version_number': VERSION_NUMBER,
	   'text_formats': TEXT_FORMATS,
	   'num_nudge_categories': NUM_NUDGE_CATEGORIES,
	   'num_tags_in_tag_set': NUM_TAGS_IN_TAG_SET,
	   'time_zone_names': pytz.all_timezones,
	   'date_formats': DateFormatStrings(),
	   'time_formats': TimeFormatStrings(),
	   'time_frames': TIME_FRAMES, 
	   'entry_types': ENTRY_TYPES,
	   'entry_types_plural': ENTRY_TYPES_PLURAL,
	   'annotation_types': ANNOTATION_TYPES,
	   'request_types': REQUEST_TYPES,
	   'helping_role_names': HELPING_ROLE_TYPES,
	   'maxlength_subject_or_comment': MAXLENGTH_SUBJECT_OR_COMMENT,
	   'maxlength_name': MAXLENGTH_NAME,
	   'maxlength_tag_or_choice': MAXLENGTH_TAG_OR_CHOICE,
	   'maxlength_number': MAXLENGTH_NUMBER,
	   # stuff about user
	   'current_user': users.get_current_user(), 
	   'user_is_admin': users.is_current_user_admin(),
	   'logout_url': users.create_logout_url("/"),
	   }
	for key in newItems.keys():
		items[key] = newItems[key]
	return items

def GetCurrentSearchForMember(member):
	if member.viewSearch:
		return member.viewSearch
	else:
		return None

def GetKeyFromQueryString(queryString, keyname):
	if queryString:
		nameAndKey = queryString.split("=")
		if len(nameAndKey) > 1:
			return nameAndKey[1]
		else:
			return None
	else:
		return None

def ItemDisplayStringForGrid(item, curating=False, showingMember=False, showDetails=False):
	# link 
	if item.__class__.__name__ == "Answer":
		if showDetails:
			if not showingMember:
				linkString = item.linkStringWithQuestionText()
			else:
				linkString = item.linkStringWithQuestionTextAndReferentLink()
		else:
			if not showingMember:
				linkString = item.linkStringWithQuestionName()
			else:
				linkString = item.linkStringWithQuestionNameAndReferentLink()
	elif item.__class__.__name__ == "Annotation":
		linkString = item.linkStringWithEntryLink()
	else:
		linkString = item.linkString()
	# name
	if not showingMember:
		if item.attributedToMember():
			if item.creator.isOnlineMember:
				if item.creator.active:
					nameString = ' (<a href="member?%s">%s</a>)' % (item.creator.key(), item.creator.nickname)
				else:
					nameString = ' (%s)' % item.creator.nickname
			else:
				if item.creator.active:
					nameString = ' (<img src="/images/offline.png" alt="offline member"><a href="member?%s">%s</a>)' % (item.creator.key(), item.creator.nickname)
				else:
					nameString = ' (<img src="/images/offline.png" alt="offline member"> %s)' % item.creator.nickname
		else:
			if item.character.active:
				nameString = ' (<a href="character?%s">%s</a>)' % (item.character.key(), item.character.name)
			else:
				nameString = ' (%s)' % item.character.name
	else:
		nameString = ""
	# curating flag
	if curating:
		if item.flaggedForRemoval:
			curateString = '<a href="flag?%s" class="imagelight"><img src="../images/flag_red.png" alt="flag" border="0"></a>' % item.key()
		else:
			curateString = '<a href="flag?%s" class="imagelight"><img src="../images/flag_green.png" alt="flag" border="0"></a>' % item.key()
	else:
		curateString = ""
	# longer text if showing details
	if showDetails:
		if item.__class__.__name__ == "Annotation":
			if item.type == "comment" or item.type == "request":
				if item.longString_formatted:
					textString = ": %s" % upToWithLink(stripTags(item.longString_formatted), DEFAULT_DETAILS_TEXT_LENGTH, '/visit/readAnnotation?%s' % item.key())
				else:
					textString = ""
			else:
				textString = ""
		elif item.__class__.__name__ == "Entry":
			textString = ": %s" % upToWithLink(stripTags(item.text_formatted), DEFAULT_DETAILS_TEXT_LENGTH, '/visit/read?%s' % item.key())
		else:
			textString = ""
	else:
		textString = ""
	return '<p>%s %s %s%s%s</p>' % (item.getImageLinkForType(), curateString, linkString, nameString, textString)

def checkedBlank(value):
	if value:
		return "checked"
	return ""

# ============================================================================================
# ============================================================================================
# HANDLERS
# ============================================================================================
# ============================================================================================

class ImageHandler(webapp.RequestHandler):
	def get(self):
		if self.request.get("member_id"):
			member = db.get(self.request.get("member_id"))
			if member and member.profileImage:
				self.response.headers['Content-Type'] = "image/jpg"
				self.response.out.write(member.profileImage)
			else:
				self.error(404)
		elif self.request.get("rakontu_id"):
			rakontu = db.get(self.request.get("rakontu_id"))
			if rakontu and rakontu.image:
				self.response.headers['Content-Type'] = "image/jpg"
				self.response.out.write(rakontu.image)
			else:
				self.error(404)
		elif self.request.get("entry_id"):
			entry = db.get(self.request.get("entry_id"))
			if entry and entry.type == "pattern" and entry.screenshotIfPattern:
				self.response.headers['Content-Type'] = "image/jpg"
				self.response.out.write(entry.screenshotIfPattern)
		elif self.request.get("character_id"):
			character = db.get(self.request.get("character_id"))
			if character:
				self.response.headers['Content-Type'] = "image/jpg"
				self.response.out.write(character.image)
		elif self.request.get("attachment_id"):
			attachment = db.get(self.request.get("attachment_id"))
			if attachment:
				self.response.headers['Content-Type'] = attachment.mimeType
				self.response.out.write(attachment.data)
			   
class AttachmentHandler(webapp.RequestHandler):
	def get(self):
		if self.request.get("attachment_id"):
			attachment = db.get(self.request.get("attachment_id"))
			if attachment and attachment.data:
				if attachment.mimeType in ["image/jpeg", "image/png", "text/html", "text/plain"]:
					self.response.headers.add_header('Content-Disposition', 'filename="%s"' % attachment.fileName)
				else:
					self.response.headers.add_header('Content-Disposition', 'attachment; filename="%s"' % attachment.fileName)
				self.response.headers.add_header('Content-Type', attachment.mimeType)
				self.response.out.write(attachment.data)
			else:
				self.error(404)
				
class ExportHandler(webapp.RequestHandler):
	def get(self):
		if self.request.get("csv_id"):
			export = db.get(self.request.get("csv_id"))
			if export and export.data:
				self.response.headers.add_header('Content-Disposition', 'export; filename="%s"' % "export.csv")
				self.response.headers.add_header('Content-Type', "text/csv")
				self.response.out.write(export.data)
			else:
				self.error(404)
		elif self.request.get("print_id"):
			export = db.get(self.request.get("print_id"))
			if export and export.data:
				self.response.headers.add_header('Content-Disposition', 'export; filename="%s"' % "print.html")
				self.response.headers.add_header('Content-Type', "text/html")
				self.response.out.write(export.data)
			else:
				self.error(404)
		elif self.request.get("xml_id"):
			export = db.get(self.request.get("xml_id"))
			if export and export.data:
				self.response.headers.add_header('Content-Disposition', 'export; filename="%s"' % "export.xml")
				self.response.headers.add_header('Content-Type', "text/xml")
				self.response.out.write(export.data)
			else:
				self.error(404)
				
# ============================================================================================
# ============================================================================================
# SITE-LEVEL DEFAULTS AND SAMPLES
# ============================================================================================
# ============================================================================================

def GenerateHelps():
	db.delete(Help.all().fetch(FETCH_NUMBER))
	file = open('help.csv')
	helpStrings = csv.reader(file)
	for row in helpStrings:
		if len(row[0]) > 0 and row[0][0] != ";":
			help = Help(type=row[0].strip(), name=row[1].strip(), text=row[2].strip())
			help.put()
	file.close()
		
def helpLookup(name, type):
	return Help.all().filter("name = ", name).filter("type = ", type).get()

def helpTextLookup(name, type):
	match = Help.all().filter("name = ", name).filter("type = ", type).get()
	if match:
		return match.text
	else:
		return None
	
def ReadQuestionsFromFile(fileName, rakontu=None, rakontuType="ALL"):
	if not rakontu:
		db.delete(Question.all().filter("rakontu = ", None).fetch(FETCH_NUMBER))
	file = open(fileName)
	questionStrings = csv.reader(file)
	questionsToPut = []
	for row in questionStrings:
		if row[0] and row[1] and row[0][0] != ";":
			if rakontuType != "ALL":
				if row[8]: 
					typesOfRakontu = [x.strip() for x in row[8].split(",")]
				else:
					typesOfRakontu = RAKONTU_TYPES[:-1] # if no entry interpret as all except custom
				logging.info(typesOfRakontu)
			if rakontuType == "ALL" or rakontuType in typesOfRakontu:
				refersTo = [x.strip() for x in row[0].split(",")]
				for reference in refersTo:
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
					typesOfRakontu = [x.strip() for x in row[8].split(",")]
					question = Question(refersTo=reference, name=name, text=text, type=type, choices=choices, multiple=multiple,
									responseIfBoolean=responseIfBoolean, minIfValue=minValue, maxIfValue=maxValue, help=help, useHelp=useHelp, rakontu=rakontu)
					questionsToPut.append(question)
	db.put(questionsToPut)
	file.close()

def GenerateSampleQuestions():
	ReadQuestionsFromFile('sample_questions.csv')
	
def GenerateDefaultQuestionsForRakontu(rakontu, type):
	ReadQuestionsFromFile('default_questions.csv', rakontu, type)
	
def GenerateDefaultCharactersForRakontu(rakontu):
	file = open('default_characters.csv')
	questionStrings = csv.reader(file)
	characters = []
	for row in questionStrings:
		if len(row) >= 4 and row[0][0] != ";":
			name = row[0]
			description = row[1]
			etiquetteStatement = row[2]
			imageFileName = row[3]
			image = db.Blob(open(imageFileName).read())
			character = RakontuCharacter(
							   name=row[0],
							   rakontu=rakontu,
							   )
			format = "plain text"
			character.description = db.Text(description)
			character.description_formatted = db.Text(InterpretEnteredText(description, format))
			character.description_format = format
			character.etiquetteStatement = db.Text(etiquetteStatement)
			character.etiquetteStatement_formatted = db.Text(InterpretEnteredText(etiquetteStatement, format))
			character.etiquetteStatement_format = format
			character.image = image
			characters.append(character)
	db.put(characters)
	file.close()
	
def GenerateSystemResources():
	db.delete(Entry.all().filter("rakontu = ", None).filter("type = ", "resource").fetch(FETCH_NUMBER))
	for i in range(len(SYSTEM_RESOURCES)):
		resourceArray = SYSTEM_RESOURCES[i]
		title = resourceArray[0]
		format = resourceArray[1]
		managersOnly = resourceArray[2]
		text = resourceArray[3]
		newResource = Entry(rakontu=None, 
						type="resource",
						title=title,
						text=text,
						text_format=format,
						text_formatted=db.Text(InterpretEnteredText(text, format)),
						creator=None,
						draft=False,
						inBatchEntryBuffer=False,
						published=datetime.now(tz=pytz.utc),
						resourceForHelpPage=True,
						resourceForNewMemberPage=True,
						resourceForManagersAndOwnersOnly=managersOnly,
						)
	 	newResource.put()
	
def CopyDefaultResourcesForNewRakontu(rakontu, member):
	systemResources = Entry.all().filter("rakontu = ", None).filter("type = ", "resource").fetch(FETCH_NUMBER)
	for resource in systemResources:
		newResource = Entry(rakontu=rakontu, 
						type="resource",
						title=systemResource.title,
						text=systemResource.text,
						text_format=systemResource.text_format,
						text_formatted=systemResource.text_formatted,
						creator=member,
						draft=False,
						inBatchEntryBuffer=False,
						published=datetime.now(tz=pytz.utc),
						resourceForHelpPage=systemResource.resourceForHelpPage,
						resourceForNewMemberPage=systemResource.resourceForNewMemberPage,
						resourceForManagersAndOwnersOnly=systemResource.resourceForManagersAndOwnersOnly,
						resourceForAllNewRakontus=False,
						)
	 	newResource.put()

def GetSystemResources():
	return Entry.all().filter("rakontu = ", None).filter("type = ", "resource").fetch(FETCH_NUMBER)
	
# ============================================================================================
# ============================================================================================
# COLORS
# ============================================================================================
# ============================================================================================

def HTMLColorToRGB(colorstring):
    colorstring = colorstring.strip()
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)

def RGBToHTMLColor(rgb_tuple):
    return '%02x%02x%02x' % rgb_tuple
	
def HexColorStringForRowIndex(index):
	if index == 0:
		return GRID_DISPLAY_ROW_COLORS_TOP
	else:
		r,g,b = HTMLColorToRGB(GRID_DISPLAY_ROW_COLORS_TOP)
		r -= index * COLOR_DECREMENT
		g -= index * COLOR_DECREMENT
		b -= index * COLOR_DECREMENT
		return RGBToHTMLColor((r,g,b))
	
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

def RelativeTimeDisplayString(whenUTC, member):
	if member and member.timeZoneName:
		when = whenUTC.astimezone(timezone(member.timeZoneName))
		delta = datetime.now(tz=timezone(member.timeZoneName)) - when
		if delta.days < 1 and delta.seconds < 1: 
			return "Now"
		elif delta.days < 1 and delta.seconds < 60: # one minute
			return "Moments ago"
		elif delta.days < 1 and delta.seconds < 60*60: # one hour
			return "%s minutes ago" % (delta.seconds // 60)
		elif delta.days < 1:
			return when.strftime(DjangoToPythonTimeFormat(member.timeFormat))
		elif delta.days < 2:
			return "Yesterday at %s" % when.strftime(DjangoToPythonTimeFormat(member.timeFormat))
		elif delta.days < 7:
			return when.strftime("%s at %s" % (DjangoToPythonDateFormat(member.dateFormat), 
											DjangoToPythonTimeFormat(member.timeFormat)))
		else:
			return when.strftime("%s at %s" % (DjangoToPythonDateFormat(member.dateFormat), 
											DjangoToPythonTimeFormat(member.timeFormat)))
	else:
		return None

# ============================================================================================
# ============================================================================================
# TEXT PROCESING
# ============================================================================================
# ============================================================================================

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

SIMPLE_HTML_REPLACEMENTS = [
							("<p>", "{{startPar}}"), ("</p>", "{{stopPar}}"),
							("<b>", "{{startBold}}"), ("</b>", "{{stopBold}}"),
							("<i>", "{{startItalic}}"), ("</i>", "{{stopItalic}}"),
							("<del>", "{{startStrike}}"), ("</del>", "{{stopStrike}}"),
							("<code>", "{{startCode}}"), ("</code>", "{{stopCode}}"),
							("<ul>", "{{startUL}}"), ("</ul>", "{{stopUL}}"),
							("<ol>", "{{startOL}}"), ("</ol>", "{{stopOL}}"),
							("<li>", "{{startLI}}"), ("</li>", "{{stopLI}}"),
							("<h1>", "{{startH1}}"), ("</h1>", "{{stopH1}}"),
							("<h2>", "{{startH2}}"), ("</h2>", "{{stopH2}}"),
							("<h3>", "{{startH3}}"), ("</h3>", "{{stopH3}}"),
							("<br/>", "{{BR}}"),
							("<hr>", "{{HR}}"),
							("&nbsp;", "{{NBSP}}")
							]

TEXT_FORMATS = ["plain text", "simple HTML", "Wiki markup"]

def InterpretEnteredText(text, mode="text"):
	result = text
	if mode == "plain text":
		result = htmlEscape(result)
		lines = result.split("\n")
		changedLines = []
		for line in lines:
			changedLines.append("<p>%s</p>" % line)
		result = "\n".join(changedLines)
	elif mode == "simple HTML":
		""" Simple HTML support:
			p, b, i, del, code, ul, ol, h1, h2, h3, br, hr, href, img
		"""
		# links
		linkExpression = re.compile(r'<a href="(.+?)">(.+?)</a>')
		links = linkExpression.findall(result)
		for url, label in links:
			result = result.replace('<a href="%s">' % url, '{{BEGINHREF}}%s{{ENDHREF}}' % url)
			result = result.replace('%s</a>' % label, '%s{{ENDLINK}}' % label)
		# image links
		imageLinkExpression = re.compile(r'<img src="(.+?)" alt="(.+?)"/>')
		imageLinks = imageLinkExpression.findall(result)
		for url, alt in imageLinks:
			result = result.replace('<img src="%s" alt="%s"/>' % (url, alt), '{{BEGINIMG}}%s|%s{{ENDIMG}}' % (url,alt))
		# bold, italic, etc
		for htmlVersion, longVersion in SIMPLE_HTML_REPLACEMENTS:
			result = result.replace(htmlVersion, longVersion)
		# now escape it
		result = htmlEscape(result)
		# bold, italic, etc
		for htmlVersion, longVersion in SIMPLE_HTML_REPLACEMENTS:
			result = result.replace(longVersion, htmlVersion)
		# links
		for url, label in links:
			result = result.replace('{{BEGINHREF}}%s{{ENDHREF}}' % url, '<a href="%s">' % url)
			result = result.replace('%s{{ENDLINK}}' % label, '%s</a>' % label)
		# image links
		for url, alt in imageLinks:
			result = result.replace('{{BEGINIMG}}%s|%s{{ENDIMG}}' % (url, alt), '<img src="%s" alt="%s"/>' % (url,alt))
	elif mode == "Wiki markup":
		result = htmlEscape(result)
		lines = result.split("\n")
		changedLines = []
		changedLines.append("<p>")
		bulletedListGoingOn = False
		numberedListGoingOn = False
		for line in lines:
			if len(line.strip()) == 0:
				changedLines.append("</p>\n<p>")
			if len(line) >= 3 and line[:3] == "===":
				if bulletedListGoingOn:
					bulletedListGoingOn = False
					changedLines.append("</ul>")
				if numberedListGoingOn:
					numberedListGoingOn = False
					changedLines.append("</ol>")
				changedLines.append("<h3>%s</h3>" % line[3:].strip())
			elif len(line) >= 2 and line[:2] == "==":
				if bulletedListGoingOn:
					bulletedListGoingOn = False
					changedLines.append("</ul>")
				if numberedListGoingOn:
					numberedListGoingOn = False
					changedLines.append("</ol>")
				changedLines.append("<h2>%s</h2>" % line[2:].strip())
			elif len(line) >= 1 and line[:1] == "=":
				if bulletedListGoingOn:
					bulletedListGoingOn = False
					changedLines.append("</ul>")
				if numberedListGoingOn:
					numberedListGoingOn = False
					changedLines.append("</ol>")
				changedLines.append("<h1>%s</h1>" % line[1:].strip())
			elif len(line) >= 3 and line[:3] == "  *":
				if not bulletedListGoingOn:
					bulletedListGoingOn = True
					changedLines.append("<ul>")
				changedLines.append("<li>%s</li>" % line[3:].strip())
			elif len(line) >= 3 and line[:3] == "  #":
				if not numberedListGoingOn:
					numberedListGoingOn = True
					changedLines.append("<ol>")
				changedLines.append("<li>%s</li>" % line[3:].strip())
			elif line.strip() == "----":
				if bulletedListGoingOn:
					bulletedListGoingOn = False
					changedLines.append("</ul>")
				if numberedListGoingOn:
					numberedListGoingOn = False
					changedLines.append("</ol>")
				changedLines.append("<hr>")
			else:
				if len(line) >= 2 and line[:2] != "  ":
					if bulletedListGoingOn:
						bulletedListGoingOn = False
						changedLines.append("</ul>")
					if numberedListGoingOn:
						numberedListGoingOn = False
						changedLines.append("</ol>")
				changedLines.append(line)
		if bulletedListGoingOn:
			changedLines.append("</ul>")
		if numberedListGoingOn:
			changedLines.append("</ol>")
		changedLines.append("</p>")
		result = "\n".join(changedLines)
		for bold in re.compile(r'\*(.+?)\*').findall(result):
			result = result.replace('*%s*' % bold, '<b>%s</b>' % bold)
		for italic in re.compile(r'\_(.+?)\_').findall(result):
			result = result.replace('_%s_' % italic, '<i>%s</i>' % italic)
		for code in re.compile(r'\^(.+?)\^').findall(result):
			result = result.replace('^%s^' % code, '<code>%s</code>' % code)
		for strike in re.compile(r'\~(.+?)\~').findall(result):
			result = result.replace('~%s~' % strike, '<span style="text-decoration: line-through">%s</span>' % strike)
		for link, name in re.compile(r'\[(.+?)\((.+?)\)\]').findall(result):
			result = result.replace('[%s(%s)]' % (link,name), '<a href="%s">%s</a>' % (link, name))
		for link in re.compile(r'\[(.+?)\]').findall(result):
			result = result.replace('[%s]' % link, '<a href="%s">%s</a>' % (link, link))
		for imageLink, alt in re.compile(r'\{(.+?)\((.+?)\)\}').findall(result):
			result = result.replace('{%s(%s)}' % (imageLink,alt), '<img src="%s" alt="%s"/>' % (imageLink, alt))
	return result

def upTo(value, number):
	if value:
		result = value[:number]
		if len(value) > number:
			result += "..."
	else:
		result = value
	return result

def upToWithLink(value, number, link):
	if value:
		result = value[:number]
		if len(value) > number:
			result += ' <a href="%s">...</a>' % link
	else:
		result = value
	return result

# ============================================================================================
# ============================================================================================
# FOR TESTING
# ============================================================================================
# ============================================================================================

def MakeSomeFakeData():
	user = users.get_current_user()
	rakontu = Rakontu(name="Test rakontu", description="Test description")
	rakontu.initializeFormattedTexts()
	rakontu.put()
	member = Member(googleAccountID=user.user_id(), googleAccountEmail=user.email(), nickname="Tester", rakontu=rakontu, governanceType="owner")
	member.initialize()
	member.put()
	if user.email() != "test@example.com":
		PendingMember(rakontu=rakontu, email="test@example.com").put()
	else:
		PendingMember(rakontu=rakontu, email="cfkurtz@cfkurtz.com").put()
	PendingMember(rakontu=rakontu, email="admin@example.com").put()
	RakontuCharacter(name="Little Bird", rakontu=rakontu).put()
	RakontuCharacter(name="Old Coot", rakontu=rakontu).put()
	RakontuCharacter(name="Blooming Idiot", rakontu=rakontu).put()
	entry = Entry(rakontu=rakontu, type="story", creator=member, title="The dog", text="The dog sat on a log.", draft=False)
	entry.put()
	entry.publish()
	annotation = Annotation(rakontu=rakontu, type="comment", creator=member, entry=entry, shortString="Great!", longString="Wonderful!", draft=False)
	annotation.put()
	annotation.publish()
	annotation = Annotation(rakontu=rakontu, type="comment", creator=member, entry=entry, shortString="Dumb", longString="Silly", draft=False)
	annotation.put()
	annotation.publish()
	entry = Entry(rakontu=rakontu, type="story", creator=member, title="The circus", text="I went the the circus. It was great.", draft=False)
	entry.put()
	entry.publish()



