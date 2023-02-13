# ping_monitor

Ping monitor script execute ping to hosts and draw RRD graphs with RTT average time from hosts. Automatically create monitor page in /var/www/html/

Script execute ping to hosts one time per 60sec
Monitor page will be refreshed automatically

1. Tested on CentOS7 clean install, python script and binary file

2. Requiremnts for execution from binary file, please install: 
                
                yum install rrdtool
                
4. Requiremnts for script execution, please install: 

        yum install epel-release
        yum update -y
        yum install python-pip rrdtool python-rrdtool gcc rrdtool-devel python-devel python-jinja2 -y
        
        pip install pyping rrdtool
        
5. installed and configured httpd service needed:

        yum install httpd -y
        systemctl enable http
        systemctl start http
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --reload
        
6. Script execution:
          execute script: python ping_monitor.py
          
          script creates empty hosts.txt file - add hosts to this file
          
          script creates folder for RRD graph and RRD DB's in /var/www/html/
          
          script creates monitor.html page in /var/www/html/
          
          access to page http://apache_server_ip/monitor.html
          
 7. Hosts file can be edited without script or binary file rexecution
 
          Warning RRD Graph and DB will be deleted. if you want save data backup RRD DB in /var/www/html/rrd_db
          
          !!! hostname or ip must be provided without dots !!!
          
          for Ex: cp /var/www/html/rrd_db/hostname.rrd /var/www/html/rrd_db/hostname.rrd.bck
          
          
        
        
        
        
