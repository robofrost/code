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

# These guys CAN go into a paragraph so no need to store in master math_dict
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
	math_dict = {}
	pseudo_dict = {}

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

		math_dict[n] = res.replace("\t", "")
		md = md.replace(res, "@{}".format(n))

		n += 1

	# Pseudocode
	for res in re.findall("\t*\&\&[^\&]+\&\&", md):

		pseudo_dict[n] = pseudocode(res.replace("&", ""))
		md = md.replace(res, "@{}".format(n))

		n += 1

	# Embeddable objects
	for reg in embeddable:
		for res in re.findall(reg, md):
			html = embeddable[reg][0].format(res.count("\t") * 40, res.replace(embeddable[reg][1], ""))
			md = md.replace(res, html)

	# Parse and convert ordered points
	for res in re.findall("\n\t*[a-zA-Z0-9]+\. [^\n]+", md):

		contents = res.strip().split(". ")

		alphanum = contents[0]
		contents = contents[1]

		html = ordered_point_template.format(res.count("\t") * 40, alphanum, contents)
		math_dict[n] = html
		md = md.replace(res, "\n@{}".format(n), 1)

		n += 1

	# Nonembeddable objects
	for reg in nonembeddable:
		for res in re.findall(reg, md):
			html = nonembeddable[reg][0].format(res.count("\t") * 40, res.replace(nonembeddable[reg][1], "").replace("\t", ""))
			math_dict[n] = html
			md = md.replace(res, "\n@{}".format(n), 1)

			n += 1

	md = md.strip()

	for num in reversed(pseudo_dict):
		md = md.replace("@{}".format(num), pseudo_dict[num])

	print(md)

	html = ""

	# List to store all pseudocode line numbers and take the maximum
	# This allows us to set a global value of the line width <p> element for the entire document
	line_nums = []

	for line in md.splitlines():

		if len(line.strip()) == 0:
			html += "<br>"

		# Mathjax
		elif line.startswith("@"):
			html += line

		# Pseudocode
		elif line[:2] in ["&&", "&*"]:

			prefix = line[:2]
			line = line[2:]

			# Extract line numbers
			line_num = line.split("$")[0].strip()
			
			# Extract contents of line (without line number)
			line = line[len(line_num):]

			# Add the line number to the global list of line numbers for the entire document
			line_nums.append(int(line_num))

			# Count how many tabs this line starts with, if any
			tabs = 0
			for char in line:
				if char == "\t":
					tabs += 1
				else:
					break

			color = ""
			font_size = ""
			if prefix == "&*":
				color = " color: blue;"
				font_size = " font-size: 0.8em;"

			html += """<div style="white-space: nowrap;"><p style="display: inline-block; font-size: 0.8em; text-align: right; width: &&LINE_NUM_WIDTH_TARGET&&px; margin-right: 30px;">$\\text{{{}:}}$</p><p style="margin-left: {}px; display: inline-block;{}{}">{}</p></div>""".format(line_num, tabs * 40, color, font_size, line.replace("\t", "")) + "\n"


		else:

			# Count how many tabs this line starts with, if any
			tabs = 0
			for char in line:
				if char == "\t":
					tabs += 1
				else:
					break

			html += """<p style="margin-left: {}px">{}</p>""".format(tabs * 40, line.replace("\t", "")) + "\n"


	max_line_num = max(line_nums)
	html = html.replace("&&LINE_NUM_WIDTH_TARGET&&", str(len(str(max_line_num)) * 10))


	for num in reversed(math_dict):
		html = html.replace("@{}".format(num), math_dict[num])

	with open("template.html") as fp:
		template = fp.read()

	template = template.replace("TITLE_TARGET", file.replace("-", " ").title())
	template = template.replace("CONTENT_TARGET", html)

	with open(out_path + file + ".html", "w") as fp:
		fp.write(template)


def generate_tabs(n):

	string = ""
	
	for i in range(n):
		string += "\t"
	
	return(string)

def generate_at_signs(n):

	string = ""
	
	for i in range(n):
		string += "@"

	return(string)

def pseudocode(string):

	keywords = [
		"for",
		"if",
		"else",
		"while",
		"to",
		"do",
		"then",
		"set",
		"end",
		"procedure",
		"function",
		"return",
		"each",
		"compute",
	]

	chars = [
		"+",
		"-",
		"/",
		"*",
		"^",
		"_",
		"=",
		"<",
		">",
		"(",
		")",
		"[",
		"]",
		"\\{",
		"\\}",
		",",
		"|",
	]

	string = string.strip()

	output = ""

	line_num = 0
	for line in string.split("\n"):


		if len(line.strip()) == 0:
			output += "&&" + str(line_num) + "\n"
			line_num += 1
			continue

		# Comment
		if line.strip().startswith("//"):

			# Count how many tabs this line starts with, if any
			tabs = 0
			for char in line:
				if char == "\t":
					tabs += 1
				else:
					break

			# Extract the text of the comment
			comment_text = line.strip()[2:].strip()

			output += "&*" + str(line_num) + generate_tabs(tabs) + "$\\text{" + comment_text + "}$\n"

			line_num += 1

			continue

		# Count how many tabs this line starts with, if any
		tabs = 0
		for char in line:
			if char == "\t":
				tabs += 1
			else:
				break

		line = " " + line + " "
		word_regex = "\\\\*\w+"

		comps_dict = {}

		n = 1
		for res in re.findall(word_regex, line):

			if "\\" in res:
				continue

			comps = res.split("_")

			for comp in comps:
				if len(comp) > 1:

					bold = ""
					if comp in keywords:
						bold = "bf"

					comps_dict[n] = "\\text" + bold + "{ " + comp + " }"
					line = line.replace(comp, generate_at_signs(n), 1)

					n += 1

		# So as not to accidentally replace anything
		for n in reversed(comps_dict):
			line = line.replace(generate_at_signs(n), comps_dict[n])

		# Fix spaces
		# These here can probably be generalized



		'''

		res = 0

		for res in re.findall("\\\\text\{ *[a-zA-z0-9]+ *}", line):

			index_0 = line.find(res)
			index_f = index_0 + len(res)

			following = line[index_f:index_f+10]

			print(following)

			if following.startswith(" \\text{ "):
				line = line.replace(res, res.replace(" }", "}"), 1)
			elif following.startswith(" \\textbf{ "):
				line = line.replace(res, res.replace(" }", "}"), 1)

		for res in re.findall("\\\\textbf\{ *[a-zA-z0-9]+ *}", line):

			index_0 = line.find(res)
			index_f = index_0 + len(res)

			following = line[index_f:index_f+10]

			print(following)

			if following.startswith(" \\text{ "):
				line = line.replace(res, res.replace(" }", "}"), 1)
			elif following.startswith(" \\textbf{ "):
				line = line.replace(res, res.replace(" }", "}"), 1)

		'''
		'''
		for char in chars:
			target_1 = char + " \\text{ "
			target_2 = " } " + char
			target_3 = " }" + char
			destination_1 = char + " \\text{"
			destination_2 = "} " + char
			destination_3 = "}" + char

			line = line.replace(target_1, destination_1)
			line = line.replace(target_2, destination_2)
		'''

		###### The only acceptable time for a word to have a space on either side is when there is another word on that side with no space


		# Add the converted line to the output string with some special formatting for communication with the master script
		output += "&&" + str(line_num) + generate_tabs(tabs) + "$" + line + "$\n"

		# Increment line number by 1
		line_num += 1
	
	return(output)