import ConfigParser

configParser = ConfigParser.RawConfigParser()
configFilePath = r'./config.cfg'
configParser.read(configFilePath)
path1 = configParser.get('config', 'PORT')

print 'path', path1;