#-*- coding: utf-8 -*-

import paramiko
import os
import threading

# 将本地文件发送到远端
def trans_file(ip, port, username, passwd, local_file, remote_file):
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip,9999,username,passwd,timeout=5)
		sftp = ssh.open_sftp();
		sftp.put(local_file, remote_file);
		ssh.close()
	except Exception:
		print '%s\tError: %s\n' % (ip, 'scp')
		return -1
	return 0

# 执行远端命令 
def ssh2(ip, port, username, passwd, cmd):
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, port, username, passwd, timeout=5)
		for m in cmd:
			stdin, stdout, stderr = ssh.exec_command(m)
#           stdin.write("Y")   #简单交互，输入 ‘Y’ 
			out = stdout.readlines()
            #屏幕输出
			for o in out:
				print o,
		ssh.close()

	except :
		print '%s\tError: %s\n'%(ip, cmd)
		return -1
	return 0

class argument:
	host = []
	username = "root"
	passwd = "asdf"
	local_file = "./"
	remote_dir = "/root/test_write/"
	conf_path = './CONF'
	exe_path = './a.out'
	exe_file = 'a.out'

	def read_argument(self):
		conf =  open(argument.conf_path, 'r')
		lines = []
		while True:
			line = conf.readline()
			if not line:
				break
			lines.append(line)
		conf.close()
		for line in lines:
			if not line.split():
				continue
			key = line.split(':')[0]
			value = line.split(':')[1]
			value = str(value).lstrip()
			value = value.replace('\n', '');
			if key == 'ssh':
				argument.host.append(value)
			elif key == 'port':
				argument.port = int(value)
			elif key == 'username':
				argument.username = value
			elif key == 'passwd':
				argument.passwd = value
			elif key == 'remote_path':
				length = len(value) - 1
				if value[length] == '/' and length != 0:
					argument.remote_dir =value[0:length+1]
				else:
					argument.remote_dir =value
		print 'host:%s' % argument.host
		print 'port:%s' % argument.port
		print 'username:%s' % argument.username
		print 'passwd:%s' % argument.passwd
		print 'remote_file:%s' % argument.remote_dir

def prepare():
	os.system('chmod 777 a.out')
	cmd = 'sed -i "/node:/d" %s' % './CONF' #删除 node 键值
	os.system(cmd)
	
	return 0

# 到目标节点执行启动测试程序
def mulit_thread(count, host, port, username, passwd, exe_file, remote_dir):
	cmd = ['mkdir %s -p' % remote_dir]#要执行的命令列表
	cmd_chmod_conf = ['chmod 664 %s/CONF'%(remote_dir)] #确保CONF文件可读
	cmd_chmod_exe = ['chmod 775 %s/%s'%(remote_dir, exe_file)] #保证a.out可执行
	cmd_exe = ['cd %s;./%s'%(remote_dir, exe_file)] #执行./a.out

	ret = ssh2(host, port, username, passwd, cmd)
	if ret != 0:
		return -1
	ret = trans_file(host, port, username, passwd, './CONF', '%s/CONF'%(remote_dir))
	if ret != 0:
		return -1
	ret = trans_file(host, port, username, passwd, './%s'%exe_file, '%s/%s'%(remote_dir, exe_file))
	if ret != 0:
		return -1
	ret = ssh2(host, port, username, passwd, cmd_chmod_conf)
	if ret != 0:
		return -1
	ret = ssh2(host, port, username, passwd, cmd_chmod_exe)
	if ret != 0:
		return -1

	cmd = [ 'sed -i "/node:/d" %s' % ('%s/CONF'%(remote_dir)) ] #node保证每个节点写入的文件不同
	ret = ssh2(host, port, username, passwd, cmd)
	if ret != 0:
		return -1
	cmd = ['echo "node: %s" >> %s'%(str(count).rjust(3, '0'), '%s/CONF'%(remote_dir))]
	ret = ssh2(host, port, username, passwd, cmd)
	if ret != 0:
		return -1
	ret = ssh2(host, port, username, passwd, cmd_exe)
	if ret != 0:
		return -1

	return 0

if __name__=='__main__':
	prepare()
	argu = argument()
	argu.read_argument()
	count = 2
	threads = []
	for i in argu.host:
		trd = threading.Thread(target=mulit_thread, args=(count, i, argu.port, argu.username, argu.passwd, argu.exe_file, argu.remote_dir))
		trd.start()
		threads.append(trd)
		count+=1

	# 本机执行的命令
	cmd = 'echo "node: 001" >> %s'% argu.conf_path
	os.system(cmd)
	cmd = './%s' % argu.exe_file
	os.system(cmd)
	
	for i in threads:
		i.join()
	del argu