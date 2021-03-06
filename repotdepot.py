# (orgit module) (by Joe)
#
# This program is non-free software; This program is licensed under a 
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 
# International License for more details.
# You should have received a copy of the Creative Commons 
# Attribution-NonCommercial-NoDerivatives 4.0 International 
# License along with this program; if not, visit:
# http://creativecommons.org/licenses/by-nc-nd/4.0/
#
#   Copyright 2014 Blue Hat Innovations <kf4jas@gmail.com>
#

import os, sys, shutil
import subprocess
import ConfigParser
import re

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

Config = ConfigParser.ConfigParser()
Config.read('/etc/orgit/config.ini')

def git(*args):
    return subprocess.check_call(['git'] + list(args))


class repodepot():
	userdir = ConfigSectionMap('mainconfig')['userdir']
	repodir = ConfigSectionMap('mainconfig')['repodir']
	orgitbin = ConfigSectionMap('mainconfig')['orgitbin']
	#print orgitbin,repodir,userdir
	folders = ['rsch','local','work','fun','learn','stor']
	musicfiletypes = ['mp3','wav','ogg']
	imagefiletypes = ['png','jpg','jpeg','bmp','gif']
	videofiletypes = ['avi','mp4']
	archivestor = ['music','video','image','docs']
	storsubs = archivestor + ['archive']

		
class setupEnv(repodepot):
	def __init__(self, possible=''):
		if possible:
			self.userdir = possible

	def makeDir(self,b,f):
		directory = "%s%s" % (b,f)
		if not os.path.exists(directory):
				os.makedirs(directory)
				print 'created',directory

	def createDirs(self, folders, addtouserdir=''):
		basedir = self.userdir+addtouserdir
		for f in folders:
			self.makeDir(basedir,f)
			
	def createALLDirs(self):
		self.makeDir(self.orgitbin)
		self.createDirs(self.folders)
		self.createDirs(self.storsubs,'stor/')
		self.createDirs(self.archivestor,'stor/archive/')

class depotcrtl(repodepot):
	def __init__(self, startdir):
		self.startdir = startdir
		self.startingdir = os.getcwd()
	def encmountctrl(self,action):
		if action == 'mount':
			print "mounting Drive"
			cmd = '/mnt'
		elif action == 'umount':
			print "Unmounting Drive"
			cmd = '/umnt'
		else:
			return False
		fullcmd = self.orgitbin+cmd
		if os.path.exists(fullcmd):
			subprocess.check_call([fullcmd])
			
	def jchown(self, path, uid, gid):
		os.chown(path, uid, gid)
		for item in os.listdir(path):
			itempath = os.path.join(path, item)
			if os.path.isfile(itempath):
				os.chown(itempath, uid, gid)
			elif os.path.isdir(itempath):
				os.chown(itempath, uid, gid)
				self.jchown(itempath, uid, gid)
	def getuserdir(self):
		return self.userdir
		
	def create(self,reponame, touchfiles):
		directory = self.userdir+self.startdir+"/"+reponame
		if not os.path.exists(directory):
			os.makedirs(directory)
			os.chdir(directory)
			for f in touchfiles:
				if not os.path.exists(f):
					open(f, 'w').close() 
			print "created", reponame
		else:
			print "Already exists"
		
	def promote(self,reponame,ldir):
		local = self.userdir+ldir+"/"
		remote = self.repodir+reponame+'.git'
		research = self.userdir+self.startdir+"/"+reponame
		newlocal = local+reponame
		if not os.getuid() == 0:
			print "you need to be root"
			sys.exit(1)
		if not os.path.exists(self.repodir):
			# I could put a mount specific store per thingy
			self.encmountctrl('mount')
		if os.path.exists(research) and os.path.exists(self.repodir):
			os.makedirs(remote)
			os.chdir(remote)
			git("init", '--bare')
			os.chdir(local)
			git("clone", remote)
			os.chdir(newlocal)	
			for f in os.listdir(research):
				shutil.move(research+"/"+f,newlocal) 
			git("add", '.')
			git("commit", "-m", '"First load from Research Directory"')
			print reponame,"promoted"
			self.jchown(newlocal,1000,1000)
			shutil.rmtree(research)
			print reponame,"Rsch repo deleted"
			self.encmountctrl('umount')
		else:
			print "Can't Promote, probly not mounted"
			sys.exit(1)
			
	def storefile(self,filename):
		os.chdir(self.startingdir)
		dire = os.getcwd()
		fullpath = dire+"/"+filename
		print fullpath
		if not os.path.exists(fullpath):
			print "WTF"
			sys.exit(1)
		else:
			farr = filename.split(".")
			farr.reverse()
			print farr[0]
			if farr[0] in self.musicfiletypes:
				shutil.move(fullpath,self.userdir+"stor/music") 
			elif farr[0] in self.imagefiletypes:
				shutil.move(fullpath,self.userdir+"stor/image") 
			elif farr[0] in self.videofiletypes:
				shutil.move(fullpath,self.userdir+"stor/video")
			else:
				print "Weird File type"

	def massivepush(self,dirlist):
		if not os.getuid() == 0:
			print "you aren't root"
			sys.exit(1)
		if not os.path.exists(self.repodir):
			# I could put a mount specific store per thingy
			self.encmountctrl('mount')
			for f in dirlist:
				u = self.userdir+f
				os.chdir(u)
				dirs=[d for d in os.listdir(u) if os.path.isdir(d)]
				for l in dirs:
					w = u+"/"+l
					os.chdir(w)
					git("add", '.')
					try:
						git("commit", "-a")
					except:
						print "nothing to commit"
					git("push","origin", "master")
			self.encmountctrl('umount')
		else:
			print "done"
			


class searchrepos(repodepot):

	def __init__(self,query):
		self.dirs = self.folders
		self.query = query
		self.zresult = []
		self.currd = ''
		
	def chunkthrough(self,dirlist):
		if len(dirlist) == 0:
			a=1
			#self.zresult
		else:
			f = dirlist.pop()
			eachrepo = self.userdir+self.currd+'/'+f
			inforead = eachrepo+"/README.md"
			#print eachrepo
			try:
				fl = open(inforead, 'r')
				#print f
				rfile = fl.readlines()
				fl.close()
				s = "%s %s %s" % ( f, rfile[0].rstrip('\n'), rfile[2].rstrip('\n') )
				if re.search(self.query,s):
					self.zresult.append({s:self.currd})
			except Exception,e:
				#print 'fail',e
				a=1
			return self.chunkthrough(dirlist)

	def walk_dirs(self):
		#print self.dirs
		if len(self.dirs) < 2:
			if self.zresult != []:
				return self.zresult
		else:
			self.currd = self.dirs.pop()
			curr = self.userdir+self.currd+'/'
			dirlist = os.listdir(curr)
			self.chunkthrough(dirlist)
			return self.walk_dirs()

	def showsearch(self,a):
		s = ''
		l = {'learn':[],'local':[],'work':[],'fun':[]}
		for o in a:
			for k,v in o.iteritems():
				l[v].append(k)
		for k,v in l.iteritems():
			s += k+"\n"
			for i in v:
				s += i[:70]+"...\n"
			s += "\n"
		return s
