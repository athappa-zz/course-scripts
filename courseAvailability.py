#!usr/bin/python
import requests

LOG_ON = False

PROTOCOL = 'https://'
DOMAIN = 'courses.students.ubc.ca'
PAGE = '/cs/main'

def log(s):
    if LOG_ON:
        print(s)

def getCourseResponse(course, section):
    dept = course[:4]
    courseNum = course[4:]
    url = PROTOCOL + DOMAIN + PAGE
    param = {
        'pname' : 'subjarea',
        'tname' : 'subjareas',
        'req' : 5,
        'dept' : dept,
        'course' : courseNum,
        'section' : section
    }
    log("sending request to " + url)
    response = requests.get(url, params=param)
    if (response.status_code == 200):
        log('request successful')
        return response
    else:
        log('request failed!')
        log('stop program')
        quit()

def getNumberForRegistration(response, attr):
    text = response.text
    index = text.find(attr)
    # assuming the number of remainging seats can be found 
    # in next 100 lines
    piece = text[index:index+100]
    index = piece.find("<strong>")
    start = index + 8 # 8 is the length of '<strong>'
    end = piece.find("</strong>")
    number = piece[start:end]
    return number

def getInstructor(response):
    text = response.text
    index = text.find('Instructor:')
    piece = text[index:index+300]
    if 'TBA' in piece:
        return 'TBA'
    else:
        start = piece.find('">') + 2
        end = piece.find('</a>')
        instructor = piece[start:end]
        return formatInstructorName(instructor)

def formatInstructorName(name):
    index = name.find(',')
    lastName = upperCaseToName(name[:index])
    firstName = upperCaseToName(name[index+2:])
    return firstName + ' ' + lastName

def upperCaseToName(name):
    return name[0] + name[1:].lower()


def printRecord(item):
    for key in item.keys():
        log(key + ': ' + str(item[key]))

def writeWeb(response):
    f = open('output/website.html', 'w')
    f.write(response.text)
    f.close()

def getCourseInfo(course, section):
    response = getCourseResponse(course, section)
    writeWeb(response)
    if checkCourseAvailable(response):
        seatsRemaining = getNumberForRegistration(response, "Total Seats Remaining")
        currRegistered = getNumberForRegistration(response, "Currently Registered")
        instructor = getInstructor(response)
        log('SeatsRemaining---' + seatsRemaining)
        log('CurrentlyRegistered---' + currRegistered)
        total = str(int(seatsRemaining) + int(currRegistered))
        return {
            'Course' : course,
            'Section' : section,
            'Instructor' : instructor,
            'SeatsRemaining' : seatsRemaining,
            'CurrentlyRegistered' : currRegistered,
            'Total' :  total
        }

def checkCourseAvailable(response):
    text = response.text
    courseNotOffered = 'The requested section is either no longer offered at UBC Vancouver or is not being offered this session.'
    if courseNotOffered in text:
        log('Course is no longer offered')
        return False
    else:
        return True

def getCourse(course, section):
    item = getCourseInfo(course, section)
    if item != None:
        printRecord(item)
        return item

def getCourseVague(course):
    sectionList = getSections(course)
    result = []
    for section in sectionList:
        courseInfo = getCourse(course, section)
        result.append(courseInfo)
    return result

def getSections(course):
    response = getSectionsResponse(course)
    return parseSections(response)

def getSectionsResponse(course):
    dept = course[:4]
    courseNum = course[4:]
    param = {
        'pname' : 'subjarea',
        'tname' : 'subjareas',
        'req' : 3,
        'dept' : dept,
        'course' : courseNum
    }
    url = PROTOCOL + DOMAIN + PAGE
    log("sending request to " + url)
    response = requests.get(url, params=param)
    if (response.status_code == 200):
        log('request successful')
        return response
    else:
        log('request failed!')
        log('stop program')
        quit()

def parseSections(response):
    text = response.text
    result = []
    index = text.find('section=')
    while index != -1:
        index += 8
        text = text[index:]
        section = text[:3]
        result.append(section)
        index = text.find('section=')
    log(result)
    result = list(filter(lambda x: x[0].isdigit(), result))
    return result

def getCourseListResponse(dept):
    url = PROTOCOL + DOMAIN + PAGE
    param = {
        'pname' : 'subjarea',
        'tname' : 'subjareas',
        'req' : 1,
        'dept' : dept
    }
    log("sending request to " + url)
    response = requests.get(url, params=param)
    if (response.status_code == 200):
        log('request successful')
        return response
    else:
        log('request failed!')
        log('stop program')
        quit()

def parseCourseList(response):
    text = response.text
    result = []
    index = text.find('course=')
    while index != -1:
        index += 7
        text = text[index:]
        section = text[:3]
        result.append(section)
        index = text.find('course=')
    result = list(map(lambda x: 'CPSC'+x, result))
    log(result)
    return result

def main():
    courseList = getCourseList('CPSC')
    courseInfo = []
    for course in courseList:
        courseInfo.extend(getCourseVague(course))
    writeReport(courseInfo)
    log('Program Complete!')

def getCourseList(dept):
    response = getCourseListResponse(dept)
    writeWeb(response)
    return parseCourseList(response)

def writeReport(courseInfo):
    f = open('output/report.txt', 'w')
    for course in courseInfo:
        s = course['Course'] + ',' + course['Section'] + ',' 
        s = s + course['Instructor'] + ',' + course['SeatsRemaining'] + ',' 
        s = s + course['CurrentlyRegistered'] + ',' + course['Total'] + '\n'
        f.write(s)
    f.close()

main()
