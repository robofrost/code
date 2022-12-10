import os
import re

in_path = "/Users/jonathanleff/Library/CloudStorage/GoogleDrive-jonbleff@gmail.com/My Drive/Notes/"
out_path = "/Users/jonathanleff/Library/CloudStorage/GoogleDrive-jonbleff@gmail.com/My Drive/leff.me/markdown-to-html/"

bullet_point_template = """

<div style="display: flex; flex-direction: row; margin-left: {}px;">

	<div style="font-size: 1.4em; line-height: 1em; display: inline-block; min-width: 40px; max-width: 40px;">&#x2022;</div>

	<p>{}</p>

</div>

""".strip()

check_box_template = """

<div style="display: flex; flex-direction: row; margin-left: {}px;">

	<input type="checkbox">

	<p style="padding-left: 0.7em;">{}</p>

</div>

""".strip()

ordered_point_template = """

<div style="display: flex; flex-direction: row; margin-left: {}px;">

	<p style="display: inline-block; font-weight: bold; min-width: 40px; max-width: 40px;">{}.</p>

	<p>{}</p>

</div>

"""

# Elements that we do not want to be picked up by the catchall <p> sweeper at the end of the script
nonembeddable = {
	"\n\t*##### [^#\n]+":["""<h5 style="margin-left: {}px">{}</h5>""", "##### "],
	"\n\t*#### [^#\n]+":["""<h4 style="margin-left: {}px">{}</h4>""", "#### "],
	"\n\t*### [^#\n]+":["""<h3 style="margin-left: {}px">{}</h3>""", "### "],
	"\n\t*## [^#\n]+":["""<h2 style="margin-left: {}px">{}</h2>""", "## "],
	"\n\t*# [^#\n]+":["""<h1 style="margin-left: {}px">{}</h1>""", "# "],
	"\n\t*\- \[ \] [^\n]+":[check_box_template, "- [ ] "],
	"\n\t*\- [^\n]+":[bullet_point_template, "- "],
	"\n\-\-\-\-*":["<hr>", ""],
}

# These guys CAN go into a paragraph so no need to store in master dictionary
embeddable = {
	"\*\*[^\*]+\*\*":["""<b style="margin-left: {}px">{}</b>""", "*"],
	"\*[^\*]+\*":["""<i style="margin-left: {}px">{}</i>""", "*"],
}

def parse(file):

	# Open the file
	with open(in_path + file + ".md") as fp:
		md = fp.read()

	# Give the regexes some breathing room on both ends
	md = "\n" + md + "\n"

	md = md.replace("\n$$", "$$")
	md = md.replace("$$\n", "$$")

	n = 0
	dictionary = {}

	# Parse and convert [links](somewhere else)
	for res in re.findall("\[[^\[\]\(\)]+\]\([^\[\]\(\)]+\)", md):

		contents = res.replace("[", "").replace("]", "").replace(")", "").split("(")

		text = contents[0]
		url = contents[1].replace("%20", "-").replace(" ", "-")

		html = '<a href="{}">{}</a>'.format(url, text)

		md = md.replace(res, html)

	# Parse and convert [[links]]
	for res in re.findall("\[\[[^\[\]\(\)]+\]\]", md):

		text = res.replace("[[", "").replace("]]", "")
		url = text.replace("%20", "-").replace(" ", "-")

		html = '<a href="{}">{}</a>'.format(url, text)

		md = md.replace(res, html)

	# MathJax
	for res in re.findall("\t*\$\$[^\$]+\$\$", md):

		dictionary[n] = res.replace("\t", "")
		md = md.replace(res, "@{}".format(n))

		n += 1

	# Embeddable objects
	for reg in embeddable:
		for res in re.findall(reg, md):
			html = embeddable[reg][0].format(res.count("\t") * 40, res.replace(embeddable[reg][1], ""))
			md = md.replace(res, html)

	# Parse and convert ordered points
	for res in re.findall("\n\t*[a-zA-Z0-9]\. [^\n]+", md):

		contents = res.strip().split(". ")

		alphanum = contents[0]
		contents = contents[1]

		html = ordered_point_template.format(res.count("\t") * 40, alphanum, contents)
		dictionary[n] = html
		md = md.replace(res, "\n@{}".format(n), 1)

		n += 1

	# Nonembeddable objects
	for reg in nonembeddable:
		for res in re.findall(reg, md):
			html = nonembeddable[reg][0].format(res.count("\t") * 40, res.replace(nonembeddable[reg][1], "").replace("\t", ""))
			dictionary[n] = html
			md = md.replace(res, "\n@{}".format(n), 1)

			n += 1

	md = md.strip()

	html = ""
	for line in md.splitlines():

		if len(line.strip()) == 0:
			pass

		elif line.startswith("@"):
			html += line

		else:

			# Count how many tabs this line starts with, if any
			tabs = 0
			for char in line:
				if char == "\t":
					tabs += 1
				else:
					break

			html += """<p style="margin-left: {}px">{}</p>""".format(tabs * 40, line.replace("\t", "")) + "\n"

	for num in reversed(dictionary):
		html = html.replace("@{}".format(num), dictionary[num])

	with open("template.html") as fp:
		template = fp.read()

	template = template.replace("TITLE_TARGET", file.replace("-", " ").title())
	template = template.replace("CONTENT_TARGET", html)

	with open(out_path + file + ".html", "w") as fp:
		fp.write(template)