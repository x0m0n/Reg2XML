import xml.etree.cElementTree as ET
import os.path
import io
import re
from configparser import ConfigParser
import xml.dom.minidom

RegFile = "InputMethods.reg"
XMLFile = RegFile.strip(".reg")+".xml"
CollectionName='Language|Chinese|Japanese'

TypeDict={'binary':"REG_BINARY",
          'dword':"REG_DWORD",
          'dlindian':"REG_DWORD_LITTLE_ENDIAN",
          'dbindian':"REG_DWORD_BIG_ENDIAN",
          'expand':"REG_EXPAND_SZ",
          'link':"REG_LINK",
          'multi':"REG_MULTI_SZ",
          'none':"REG_NONE",
          'qwrod':"REG_QWORD",
          'qlindian':"REG_QWORD_LITTLE_ENDIAN",
          'sz':"REG_SZ",
          ' ':' '}
clsid={'entries':'{9CD4B2F4-923D-47f5-A062-E897DD1DAD50}',
       'collections':'{53B533F5-224C-47e3-B01B-CA3B3F3FF4BF}',
       'settings':'{A3CCFC41-DFDB-43a5-8D26-0FE8B954DA51}'}


GlobalDebug=False

class RegData:
    """Creates the registry data. Each hive key is an object and the values are part of values array"""
    def __init__(self,hive):
        self.hive=hive
        #Extract hive:
        self.hives=tuple(hive.strip('[').strip(']').split('\\'))
        self.name=[]
        self.value=[]
    def appendValue(self,name,value):
        name = name.strip('"')
        #Determines data type from value
        if value.startswith('"') and value.endswith('"'):
            DataType='sz'
            value=value.strip('"')
        elif value.startswith('hex') or value.endswith(",\\"):
            DataType='binary'
            value=value.strip('hex:').strip("\\").replace(",","").strip()
        elif value.startswith('dword'):
            DataType='dword'
            value=value.strip('dword:')
        elif value.startswith('qword'):
            value=value.strip('qword:')
            DataType='qword'
        else:
            DataType='binary'
            value=value.replace(",","").strip()
        #Redefine name so it maches the formatting of the self.name elements
        name = (name,DataType,)

        if name in self.name:
            i=self.name.index(name)
##            print("name has ",len(self.name))
##            print(self.name)
##            print("value has ",len(self.value))
##            print(self.value)
##            print("index is ",i)
##            print("Current hive is ",self.hives)
##            print("Last item on name is ",self.name[-1])
##            print("Last item on value is ",self.value[-1])
            self.value[i]=self.value[i]+value
        else:
            self.name.append(name)
            self.value.append(value)
    def getNames(self):
        return self.name
    def getValues(self,name):
        return self.value[self.name.index(name)]
    def getHives(self):
        return self.hives

def read_reg_simple(filename,encoding='utf-16'):
    with io.open(filename,encoding=encoding) as f:
        data=f.read()
        # get rid of non-section strings in the beginning of .reg file
        data = re.sub(r'^[^\[]*\n', '', data, flags=re.S)
        tempStr = ""
    for item in data:
        tempStr=tempStr+item
    data=tempStr.split('\n')
    keys = []
    name=''
    for item in data:
        if item.strip(' ')=='':
            continue
        if item.startswith('[') and item.endswith(']'):
            keys.append(RegData(item))
            name=''
        else:
            if '=' in item:
                temp = item.split('=')
                name=temp[0]
                keys[-1].appendValue(name,temp[1])
            if not('=' in item):
                keys[-1].appendValue(name,item)
    for item in keys:
        print(item.getHives())
        for name in item.getNames():
            print(name,'=',item.getValues(name),", type=",TypeDict[name[1]])

    root=ET.Element('RegistrySettings',{'clsid':clsid['settings'],'disabled':'0'})
    Collection=ET.SubElement(root,'Collection',{'clsid':clsid['collections'],'name':CollectionName})
    for item in keys:
        hive = item.getHives()
        names=item.getNames()
        for name in names:
            value=item.getValues(name)
            Registry = ET.SubElement(Collection,'Registry',{'clsid':clsid['entries'],'image':'12','name':name[0]})
            Properties = ET.SubElement(Registry,'Properties',{'action':'U','hive':hive[0],'key':'\\'.join(hive[1:]),'name':name[0],'type':TypeDict[name[1]],'value':value})

    prettyStr=xml.dom.minidom.parseString(ET.tostring(root,'utf-8')).toprettyxml()
    Tree=ET.ElementTree(ET.fromstring(prettyStr))
    Tree.write(XMLFile)

def read_reg(filename,encoding='utf-16'):
    with io.open(filename,encoding=encoding) as f:
        data=f.read()
        # get rid of non-section strings in the beginning of .reg file
        data = re.sub(r'^[^\[]*\n', '', data, flags=re.S)
        cfg = ConfigParser(strict=False)
        # dirty hack for "disabling" case-insensitive keys in "configparser"
        cfg.optionxform=str
        cfg.read_string(data)
        data = []
        # iterate over sections and keys and generate `data` for pandas.DataFrame
        for s in cfg.sections():
            if not cfg[s]:
                data.append([s, None, None, None])
            for key in cfg[s]:
                tp = val = None
                if cfg[s][key]:
                    # take care of value type
                    if ':' in cfg[s][key]:
                        tp, val = cfg[s][key].split(':')
                    else:
                        val = cfg[s][key].replace('"', '').replace(r'\\\n', '')
                data.append([s, key.replace('"', ''), tp, val])
    print(data[2])

read_reg_simple(RegFile)



##Tree = ET.parse('Sample.xml')
##root = Tree.getroot()
##prettyStr=xml.dom.minidom.parse('Sample.xml').toprettyxml()
###prettyStr=xml.dom.minidom.parseString(ET.tostring(root,'utf-8')).toprettyxml()
###Tree=ET.ElementTree(ET.fromstring(prettyStr))
##print(prettyStr)
##root=ET.fromstring(prettyStr)
##Tree=ET.ElementTree(root)
##Tree.write('SamplePretty.xml')
