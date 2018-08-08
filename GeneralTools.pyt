import arcpy, csv, os, operator, os.path
#register the dialect for windows csv
csv.register_dialect("windcsv", lineterminator="\n")
		
def sortTable(table, cols):
	""" sort a table by multiple columns
	table: a list of lists (or tuple of tuples) where each inner list
	represents a row
	cols:  a list (or tuple) specifying the column numbers to sort by
	e.g. (1,0) would sort by column 1, then by column 0
	"""
	for col in reversed(cols):
		table = sorted(table, key=operator.itemgetter(col))
	return table
	

class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the
		.pyt file)."""
		self.label = "General Tools"
		self.alias = "General Tools"
		
		# List of tool classes associated with this toolbox
		self.tools = [transcribeGeometry , documentGeodatabase, genGoogleMapsField, joinlessJoin, directoryStructureToCSV, genWebLinkField, EmbedOneToManyOverlapField, updateAcres, checkIfFilesExist]

class directoryStructureToCSV(object):
	"""generates a csv that contains all of the folders contained inside of a directory structure"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Directory Structure to CSV"
		self.description = "Writes csv file containing all folders nested inside of a folder"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""input parameters for tool """
		
		dirPath = arcpy.Parameter(name="dirPath" ,
			displayName="dirPath",
			direction="Input",
			datatype="DEFolder",
			parameterType="Required")
		
		csvPath = arcpy.Parameter(name="csvPath" ,
			displayName="csvPath",
			direction="Output",
			datatype="DEFile",
			parameterType="Required")
			
		
		return [dirPath, csvPath]
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#set up main parameters
		dirPath = str(parameters[0].valueAsText)
		csvPath = str(parameters[1].valueAsText)
		
		#open and set the csv file for writting
		opener = open(csvPath, "w")
		csvWriter = csv.writer(opener, "windcsv")
		csvWriter.writerow(["Directory"])
		
		#loop through the directory structure
		for root, dirs, files in os.walk(dirPath):
			csvWriter.writerow([root])
		
		#close out the csv file
		del csvWriter
		opener.close()
		
		
class joinlessJoin(object):
	"""tool that moves an attribute from one table to another based on a common key field"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Joinless Join"
		self.description = "moves an attribute from one table to another given key values from both tables"
		self.canRunInBackground = False
	
	def getParameterInfo(self):
		#source table
		sourceTable = arcpy.Parameter(name="sourceTable" ,
			displayName="Source Table",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#source key field
		sourceKeyField = arcpy.Parameter(name="sourceKeyField" ,
			displayName="Source Key Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the id field here within the source layer
		sourceKeyField.parameterDependencies = [sourceTable.name]
		
		#interest field in the source table
		sourceInterestField = arcpy.Parameter(name="sourceInterestField" ,
			displayName="Source Interest Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the id field here within the source layer
		sourceInterestField.parameterDependencies = [sourceTable.name]
		
		
		
		
		#target table
		targetTable = arcpy.Parameter(name="targetTable" ,
			displayName="Target Table",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#target key field
		targetKeyField = arcpy.Parameter(name="targetKeyField" ,
			displayName="target Key Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the id field here within the source layer
		targetKeyField.parameterDependencies = [targetTable.name]
		
		#target interest field
		targetInterestField = arcpy.Parameter(name="targetInterestField" ,
			displayName="Target Interest Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the id field here within the source layer
		targetInterestField.parameterDependencies = [targetTable.name]
		
		return [sourceTable, sourceKeyField, sourceInterestField, targetTable, targetKeyField, targetInterestField]
		
	
	def executeByScript(self, sourceTable, sourceKeyField, sourceInterestField, targetTable, targetKeyField, targetInterestField, messages):
		"""method allows of the tool object to be run by another tool within the same toolbox whithout regenerating the parameter objects within the other tool"""
		#get the parameters for the tool
		params = self.getParameterInfo()
		
		#write the method arguments into each of the parameter objects so the tool can run
		params[0] = sourceTable
		params[1].value = sourceKeyField
		params[2].value = sourceInterestField
		params[3].value = targetTable
		params[4].value = targetKeyField
		params[5].value = targetInterestField
		
		#execute the main tool using the falsly generated parameter objects
		self.execute(params, messages)
		
	
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#check the parameter type for the first parameter.
		if type(parameters[0]) == type(arcpy.Parameter):#if a parameter object is the first parameter then set the source table to a text version of that parameter
			sourceTable = str(parameters[0].valueAsText)
		else:#if the input parameter is another type such as a layer object then simply set the source table to equal that value
			sourceTable = parameters[0]
		
		#set the rest of the parameters for the source table
		messages.AddMessage("Source Table is " + str(sourceTable))
		sourceKeyField = str(parameters[1].valueAsText)
		messages.AddMessage("Source Key Field is " + sourceKeyField)
		sourceInterestField = str(parameters[2].valueAsText)
		messages.AddMessage("Source Interest Field is " + sourceInterestField)
		
		#set the rest of the parameters for the target table
		targetTable = str(parameters[3].valueAsText)
		messages.AddMessage("Target Table is " + targetTable)
		targetKeyField = str(parameters[4].valueAsText)
		messages.AddMessage("Target Key Field is " + targetKeyField)
		targetInterestField = str(parameters[5].valueAsText)
		messages.AddMessage("Target interest Field is " + targetInterestField)
		
		#open a cursor in the target table
		count = 0#set a progress counter to let the user know how far the tool has progressed
		upCur = arcpy.da.UpdateCursor(targetTable , [targetKeyField , targetInterestField])#make an update cursor for the target table and loop through each of its records
		for targetRow in upCur:
			#generate an sql expression that limits how many features are in the cursor so the script runs 2x as fast
			sqlLimiterForSpeed = '"' + sourceKeyField + '" = ' +  "'"  + targetRow[0] + "'"
			#open a cursor in the source table
			sCur = arcpy.da.SearchCursor(sourceTable, [sourceKeyField, sourceInterestField], where_clause=sqlLimiterForSpeed)
			for sourceRow in sCur:
				
				#if the value matches between tables then transfer it into the target table
				if targetRow[0] == sourceRow[0]:
					targetRow[1] = sourceRow[1]
					upCur.updateRow(targetRow)
			count = count + 1#progress the counter because it has finished with one record's worth of work
			messages.AddMessage("on Record in Target which is number: " + str(count))#display the current record number to the user through the dialog box


class genGoogleMapsField(object):
	"""tool that generates a field which contains links to google maps"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Generate Google Maps Field"
		self.description = "writes to a field the point location's google link to that location using lat and long coordinates"
		self.canRunInBackground = False
	
	def getParameterInfo(self):
		"""defines the tools parameters"""
		#input feature class
		inputFeatureLayer = arcpy.Parameter(name="inputFeatureLayer" ,
			displayName="Input Feature Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#google link field
		#id field for the source vector field which will be used to find out which geometries will be transfered
		googleLinkField = arcpy.Parameter(name="googleLinkField" ,
			displayName="Google Link Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines the dependce between the field and the table so it limits the drop down to the fields in the input feature class
		googleLinkField.parameterDependencies = [inputFeatureLayer.name]
		
		return [inputFeatureLayer, googleLinkField]
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#set the input parameters
		inputFeatureLayer = str(parameters[0].valueAsText)
		googleLinkField = str(parameters[1].valueAsText)
		
		messages.AddMessage("starting to translate to google links")
		#open curosr so it can perform updates on the field
		upCur = arcpy.da.UpdateCursor(inputFeatureLayer , ["SHAPE@" , googleLinkField])
		
		wgscs = arcpy.SpatialReference(4326)#generate a spatial refernce object for wgs84 coordinate system using the registration number
		
		for row in upCur:#loop through all of the features in the input table
			latLogShape = row[0].projectAs(wgscs).trueCentroid#project shape into WGS84
			
			#get the shapes new x, y coords
			x = str(round(latLogShape.X, 7))#rounding number DARIN
			y = str(round(latLogShape.Y, 7))#rounding number DARIN
			
			#construct the google string
			googleLinkString = "https://www.google.com/maps/place/" + y + "," + x#string Math for Final output DARIN

			#committ and apply the changes to the google field
			row[1] = googleLinkString
			upCur.updateRow(row)#required for the changes to perminatly take in the row
		
		
class transcribeGeometry(object):
	"""tool that generates ids for parks based on the current highest park id of outdoor grants"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Transcribe Geometry"
		self.description = "transfers geometry from one layer to another based on a common id"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""Define parameter definitions"""
		
		#contains the vector source layer from which geometry will be taken from
		sourceLayer = arcpy.Parameter(name="sourceLayer" ,
			displayName="Source Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#id field for the source vector field which will be used to find out which geometries will be transfered
		sourceIDField = arcpy.Parameter(name="sourceIDField" ,
			displayName="Source ID Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the id field here within the source layer
		sourceIDField.parameterDependencies = [sourceLayer.name]
		
		
		#where the geometry will be transfered to
		targetLayer = arcpy.Parameter(name="targetLayer" ,
			displayName="Target Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		
		#id field for the target layer which will help determine which geometries will be transfered
		targetIDField = arcpy.Parameter(name="targetIDField" ,
			displayName="Target ID Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#defines that the field here within the parks layer
		targetIDField.parameterDependencies = [targetLayer.name]
		
			
		#returns the parameters to the end user
		params = [sourceLayer , sourceIDField, targetLayer, targetIDField]
		return params
		
	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True

	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#harvest the input parameter for use in the tool
		sourceLayer = parameters[0].Value#source layer
		sourceIDField = parameters[1].valueAsText#source id field
		targetLayer = parameters[2].Value#target layer
		targetIDField = parameters[3].valueAsText#target layer's id field
		
		sCur = arcpy.da.SearchCursor(sourceLayer,  [sourceIDField, "SHAPE@"])#open a search cursor to find the list of park ids
		
		#loop through every feature in the source layer
		for sRow in sCur:
			
			upCur = arcpy.da.UpdateCursor(targetLayer,  [targetIDField, "SHAPE@"])
			for upRow in upCur:
				#if the ids match
				if sRow[0] == upRow[0]:
					#change the geometry over
					upRow[1] = sRow[1]
					
					#update the row to commit the changes to the layer
					upCur.updateRow(upRow)
					
			del upCur#delete the cursor to prevent schema locks
			
		del sCur#delete the cursor to prevent schema locks		

		
class documentGeodatabase(object):
	"""tool that generates geodatabase documentation for field schemas and other information"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Document Geodatabase"
		self.description = "document the geodatabase in great detail"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""Define parameter definitions"""
		
		#workspace that will be documented parameter
		workspacePath = arcpy.Parameter(name="workspacePath" ,
			displayName="Workspace Path",
			direction="Input",
			datatype="DEWorkspace",
			parameterType="Required")
			
		#csvPath that will be written to parameter
		csvPath = arcpy.Parameter(name="csvPath" ,
			displayName="CSV Path",
			direction="Output",
			datatype="DETable",
			parameterType="Required")
			
		#returns the parameters to the end user
		params = [workspacePath , csvPath]
		
		return params
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#grab the parameters from the parameter objects
		workspacePath = str(parameters[0].valueAsText)
		csvPath = str(parameters[1].valueAsText)
		
		
		#open a new csv document and fill out the headers
		messages.AddMessage("opening csv")
		opener = open(csvPath, "w")
		csvWriter = csv.writer(opener, "windcsv")
		
		
		#walk through all spatial data within the workspace
		messages.AddMessage("walking through all spatial data within the workspace")
		walk = arcpy.da.Walk(workspacePath)
		
		workspacePathList = []
		
		for dirworkspacePath, dirnames, filenames in walk:
			for filename in filenames:
				#make a list of the things to look at
				workspacePathList.append(os.path.join(dirworkspacePath, filename))
		messages.AddMessage("finished walking through data")
				
		#loop through workspacePaths for gis data
		for gisworkspacePath in workspacePathList:
			messages.AddMessage("entering documentation info for: " + gisworkspacePath)
			
			hasFields = True
			try:
				fieldsList = arcpy.ListFields(gisworkspacePath)
			except:
				messages.AddMessage("Object does not support fields")
				
				csvWriter.writerow(["" , "", "" , "" , "" , ""])
				csvWriter.writerow([os.path.split(gisworkspacePath)[1], "Does not Support Fields"])
				hasFields = False
			
			if hasFields == True:
				csvWriter.writerow(["" , "", "" , "" , "" , ""])
				csvWriter.writerow(["Layer or Feature Class" , "field Name", "field Alias" , "field Type" , "Length" , "Domain"])
				
				#loop through all the fields inside of the dataset
				count = 0
				for field in fieldsList:
					if count == 0:
						csvWriter.writerow([os.path.split(gisworkspacePath)[1] , str(field.baseName) , str(field.aliasName) , str(field.type) , str(field.length) , str(field.domain)])
					else:
						csvWriter.writerow(["" , str(field.baseName) , str(field.aliasName) , str(field.type) , str(field.length) , str(field.domain)])
					count += 1
		
		#space out the domains info from everything else
		csvWriter.writerow(["" , "", "" , "" , "" , ""])
		
		#loop through all the domains in the dataset
		messages.AddMessage("listing domains")
		domains = arcpy.da.ListDomains(workspacePath)
		
		if len(domains) == 0:
			csvWriter.writerow("Database does not have any domains")
		else:
			
			#domains to loop through
			messages.AddMessage("looping through domains")
			for domain in domains:
				#generate a spacer row
				csvWriter.writerow(["" , "", "" , "" , "" , ""])
				
				#write the main info about the domain
				csvWriter.writerow(["Name" , "Domain Type", "Field Type" , "Coded Values (if Relivent)" , "Coded Value Description (if Relivent)" , ""])
				csvWriter.writerow([str(domain.name) , str(domain.domainType) , str(domain.type) ,  "" , "" , ""])
				
				#loop through coded values within the domain if it has coded values
				if str(domain.domainType) == "CodedValue":
					for code in domain.codedValues:
						csvWriter.writerow(["" , "" , "" ,  str(code) , domain.codedValues[code] , ""])
						
						
		messages.AddMessage("closing worksheetthing")
		del csvWriter
		opener.close()
		
		
class genWebLinkField(object):
	"""tool that generates ids for parks based on the current highest park id of outdoor grants"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Generate Web Link Field"
		self.description = "Makes a web link field based on the extent of the associated features"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""Define parameter definitions"""
		
		#id field for the source vector field which will be used to find out which geometries will be transfered
		inputLayer = arcpy.Parameter(name="inputLayer" ,
			displayName="Input Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#field the info will be put into
		webLinkField = arcpy.Parameter(name="webLinkField" ,
			displayName="Web Link Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
			
		#defines that the id field here within the source layer
		webLinkField.parameterDependencies = [inputLayer.name]
		
		
		#parameter to define the head of the url link to the web app
		urlHead = arcpy.Parameter(name="urlHead" ,
			displayName="URL Head",
			direction="Input",
			datatype="GPString",
			parameterType="Required")
		
			
		#returns the parameters to the end user
		params = [inputLayer , webLinkField , urlHead]
		return params
		
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#harvest the input parameter for use in the tool
		inputLayer = parameters[0].Value#source layer
		webLinkField = parameters[1].valueAsText#web link field
		urlHead = parameters[2].valueAsText#url head string
		
		
		wgscs = arcpy.SpatialReference(4326)#generate a spatial refernce object for wgs84 coordinate system using the registration number
				
		upCur = arcpy.da.UpdateCursor(inputLayer,  ["SHAPE@" , webLinkField])
		for upRow in upCur:
			
			extentObj = upRow[0].projectAs(wgscs).extent
			
			extentString = "&extent=" + str(extentObj.XMin) + "," + str(extentObj.YMin) + "," + str(extentObj.XMax) + "," + str(extentObj.YMax)
			
			upRow[1] = str(urlHead) + extentString
			
			#update the row to commit the changes to the layer
			upCur.updateRow(upRow)
		
		
		del upCur#delete the cursor to prevent schema locks	
		
		
class EmbedOneToManyOverlapField(object):
	"""tool that generates ids for parks based on the current highest park id of outdoor grants"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Embed One to Many Overlap Field"
		self.description = "copies a field from a origin layer to an input layer if the features overlap. if multiple features in the origin layer overlap a single input feature both record values are combined into a single string"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""defines the tools parameters"""
		#input feature class
		inputLayer = arcpy.Parameter(name="inputLayer" ,
			displayName="Input Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#field to update
		inputField = arcpy.Parameter(name="inputField" ,
			displayName="Input Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#define layer dependency
		inputField.parameterDependencies = [inputLayer.name]
		
		#string origin feature class
		originLayer = arcpy.Parameter(name="originLayer" ,
			displayName="Origin Layer",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
		
		#string origin field
		originField = arcpy.Parameter(name="originField" ,
			displayName="Origin Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#define layer dependency
		originField.parameterDependencies = [originLayer.name]
		
		return [inputLayer, inputField, originLayer, originField]
			
	
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#parameters for input layer
		inputLayer = parameters[0].Value
		inputField = parameters[1].valueAsText
		
		#parameters for origin layer
		originLayer = parameters[2].Value
		originField = parameters[3].valueAsText
		
		#let the user know what phase its at
		messages.AddMessage("looping through origin layer")
		
		#make a list of the origin feature class feature and field of interest
		sCur = arcpy.da.SearchCursor(originLayer , ["SHAPE@", originField])
		
		originTextFeatureList = []#list that stores the origin text feature class
		
		#loop through and place in the list of features
		for row in sCur:
			originTextFeatureList.append([row[0] , row[1]])
		
		upCur = arcpy.da.UpdateCursor(inputLayer , ["SHAPE@", inputField])
		
		
		#let the user know what part you are on
		messages.AddMessage("looping through input layer")
		
		#loop through the entire input feature class
		for row in upCur:
			
			#list of text features touching input features
			touchingFeatures = []
			
			#loop through the entire text layer list
			for textFeature in originTextFeatureList:
				
				#if the features are not disjoint (aka touching) add them to the list
				if row[0].disjoint(textFeature[0]) == False:
					touchingFeatures.append(textFeature)
			
			messages.AddMessage(str(touchingFeatures))
			
			#make a string to write into the cursor
			if len(touchingFeatures) == 0:
				continue#if it is not touching any features then continue to the next item in the loop
			elif len(touchingFeatures) == 1:#special handeling if there is just one feature touching
				writeString = touchingFeatures[0][1]
			else:#create a string to write by looping through all the touching features
				
				writeString = ""#make string object in outer scope to keep adding to
				counter = 0#counter to keep track of the first iteration
				
				for feature in touchingFeatures:
					if counter == 0:#if its the first one intersected feature then treat it appropretly
						writeString += str(feature[1])
					else:
						writeString += ", " + str(feature[1])
					#advance the counter
					counter += 1
					
			#write the resulting string
			row[1] = writeString
			upCur.updateRow(row)#update the info in the main table
			
		del upCur
		
		#let the user know what part you are on
		messages.AddMessage("Finishing out script")

class updateAcres(object):
	"""loops through all feature classes in database and updates their acres field"""
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Update Acres"
		self.description = "loops through all feature classes in database and updates their acres field"
		self.canRunInBackground = False
		
		self.fieldOfInterest = "calc_acre"
		
	def getParameterInfo(self):
		"""defines the tools parameters"""
		#geodatabase that will be documented parameter
		geodatabase = arcpy.Parameter(name="geodatabase" ,
			displayName="Geodatabase Path",
			direction="Input",
			datatype="DEWorkspace",
			parameterType="Required")
			
		return [geodatabase]
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		
		#assign values that make sence to each of the variables
		geodatabase = str(parameters[0].valueAsText)
		
		#walk through all spatial data within the workspace
		messages.AddMessage("walking through all spatial data within the geodatabse " + geodatabase)
		walk = arcpy.da.Walk(geodatabase)
		
		workspacePathList = []
		workspacePathListHasFieldOfInterest = []
		
		for dirworkspacePath, dirnames, filenames in walk:
			for filename in filenames:
				#make a list of the things to look at
				workspacePathList.append(os.path.join(dirworkspacePath, filename))
				
		messages.AddMessage("finished walking through data: " + str(len(workspacePathList)) + "files found")
		
		#loop through workspacePaths for gis data
		for gisworkspacePath in workspacePathList:
			messages.AddMessage("checking dataset for field of interest: " + gisworkspacePath)
			
			hasFields = True
			try:
				fieldsList = arcpy.ListFields(gisworkspacePath)
			except:
				messages.AddMessage("Object does not support fields")
			
			if hasFields == True:
				#loop through all the fields inside of the dataset
				for field in fieldsList:
					if field.name == self.fieldOfInterest:
						workspacePathListHasFieldOfInterest.append(gisworkspacePath)
		
		#check to see if there are any feature classes with the field of interest at all
		if len(workspacePathListHasFieldOfInterest) == 0:
			messages.AddMessage("entire geodatabase lacks fields")
		else:
			#do the field calcuations for each of the feature classes involved
			for path in workspacePathListHasFieldOfInterest:
				
				messages.AddMessage("updating acres for " + path)
				
				with arcpy.da.UpdateCursor(path, ["SHAPE@AREA" , self.fieldOfInterest]) as upcur:
					for row in upcur:
						if not(row[0] == "" or row[0] == None or row[0] == "Null"):#make sure the field has a value before trying to calculate it
							acres = row[0] * 0.000247105#convert square meters to acres
							row[1] = acres
							upcur.updateRow(row)
		
		messages.AddMessage("finished script.")

	
class checkIfFilesExist(object):
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Check If Files Exist"
		self.description = "Tool that check a field contents to see if urls in the field point to files that actually exist on the drive"
		self.canRunInBackground = False
	
	def getParameterInfo(self):
		"""defines the tools parameters"""
		
		#source table
		sourceTable = arcpy.Parameter(name="sourceTable" ,
			displayName="Source Table",
			direction="Input",
			datatype="GPFeatureLayer",
			parameterType="Required")
			
		#field with links
		linkField = arcpy.Parameter(name="linkField" ,
			displayName="Link Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		#define layer dependency
		linkField.parameterDependencies = [sourceTable.name]
		
		#field for outputs
		statusField = arcpy.Parameter(name="statusField" ,
			displayName="Status Field",
			direction="Input",
			datatype="Field",
			parameterType="Required")
		
		statusField.parameterDependencies = [sourceTable.name]
		
		#define layer dependency
		return [sourceTable , linkField, statusField]
		
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		#inputs from the tool user
		sourceTable = parameters[0].Value
		linkField = parameters[1].valueAsText
		statusField = parameters[2].valueAsText
		
		messages.AddMessage("checking if files exist")
		
		#open a new cursor
		with arcpy.da.UpdateCursor(sourceTable, [linkField , statusField]) as upcur:
			
			for row in upcur:
				#check to see if file exists. then log result to field
				if os.path.isfile(row[0]):
					row[1] = "active"
				else:
					row[1] = "broken"
				
				#update the underlaying information
				upcur.updateRow(row)
			