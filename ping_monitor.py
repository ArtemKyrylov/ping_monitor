from time import sleep
import os
import argparse
import pyping
from threading import Thread
import rrdtool
from jinja2 import Environment
import datetime

SLEEP_TIME = 60
HOSTS_FILE = "hosts.txt"
RRD_DB_FOLDER_NAME = "/var/www/html/rrd_db"
RRD_GRAPH_FOLDER_NAME = "/var/www/html/rrd_graph"
RRD_GRAPH_FOLDER_NAME_HTML = "rrd_graph"
HOSTS_LIST = []
RESPONCE_DATA = {}
MONITOR_FILE = "/var/www/html/monitor.html"
GRAPH_LIST = []
HTML = """
<html>
<head>
<meta http-equiv="refresh" content="60" />
<title>monitor_page</title>
</head>
<body>
<table>
<tr>
{% for image_source in images %}
  <td><img src="{{ image_source }}"></td>
  {% if (loop.index0 % 4) == 3 %}
  </tr>
  {% endif %}
{% endfor %}
</tr>
</table>
</body>
</html>
"""


class FileWorker:

    def __init__(self, file_name):

        self.file_name = file_name

    def check_if_file_exists(self):

        if os.path.isfile(self.file_name):

            return True
        else:

            return False


    def check_if_file_not_empty(self):

        if os.stat(self.file_name).st_size == 0:

            return False
        else:

            return True


    def read_file(self):

        lines = []

        with open(self.file_name, "r+") as file:

            line_list = file.readlines()

        for item in line_list:

            line = ''.join(item)

            line = line.replace('\n', '')

            lines.append(line)

        return lines


            


    def create_file(self):

        file = open(self.file_name, "w+")

        file.close()


class FolderWorker:

    def __init__(self, folder_name):

        self.folder_name = folder_name

    def check_if_folder_exists(self):

        if os.path.exists(self.folder_name):

            return True
        else:

            return False

    def create_folder(self):

        os.mkdir(self.folder_name)


class CheckConnection(Thread):

    def __init__(self, url, name):

        Thread.__init__(self)

        self.name = name

        self.url = url


    def run(self):

        r = pyping.ping(self.url)

        RESPONCE_DATA.update({self.url: r.avg_rtt})
        

def check_hosts_file(HOSTS_FILE):

    hosts_file_obj = FileWorker(HOSTS_FILE)

    hosts_file_status = hosts_file_obj.check_if_file_exists()

    if hosts_file_status:

        print("Info: Hosts file exists")
        
        hosts_file_size = hosts_file_obj.check_if_file_not_empty()

        if hosts_file_size:

            print("Info: Hosts file not empty")

            return True, hosts_file_obj

        else:

            print("Error: Hosts file empty")

            print("Please add hosts to file line by line, for example: www.facebook.com")

            return False, hosts_file_obj

    else:

        print("Error: Hosts file does not exists and will be created")

        hosts_file_obj.create_file()

        hosts_file_status = hosts_file_obj.check_if_file_exists()

        if hosts_file_status:

            print("Info: Creating hosts file txt: please add hosts to file line by line, for example: www.facebook.com")

            print("Info: Hosts file created")

            return False, hosts_file_obj

        else:

            print("Error: Hosts file does not created")

            return False, hosts_file_obj


def collect_hosts(hosts_file_obj):

    host = hosts_file_obj.read_file()

    for item in host:

        HOSTS_LIST.append(item)

    del hosts_file_obj


def get_connection_hosts_info(HOSTS_LIST):

    threads = []

    for item, url in enumerate(HOSTS_LIST):

        name = "Stream %s" % (item + 1)

        thread = CheckConnection(url, name)

        threads.append(thread)

        thread.start()

    for thread in threads:

        thread.join()


def check_if_folder_exists_or_create_it(FOLDER_NAME):

    rrd_db_folder_obj = FolderWorker(FOLDER_NAME)

    rrd_folder_status = rrd_db_folder_obj.check_if_folder_exists()
    
    if rrd_folder_status:

        del rrd_db_folder_obj

    else:

        rrd_db_folder_obj.create_folder()

        del rrd_db_folder_obj


def check_if_rrd_db_exists_or_create_it(RRD_DB_FOLDER_NAME, HOSTS_LIST):

    for item in HOSTS_LIST:

        hostname = ''.join(item)

        hostname = hostname.replace(".", "")

        path_to_db = RRD_DB_FOLDER_NAME + "/" + hostname + ".rrd"

        rrd_base_obj = FileWorker(path_to_db)

        rrd_base_status = rrd_base_obj.check_if_file_exists()

        if rrd_base_status:

            del rrd_base_obj

            continue

        else:
            rrdtool.create(path_to_db, '--step', '60s', 'DS:' + hostname + ':GAUGE:120:0:999', 'RRA:LAST:0.5:1:1500')

            del rrd_base_obj


def check_if_rrd_graph_exists_or_create_it(RRD_GRAPH_FOLDER_NAME, RRD_DB_FOLDER_NAME, HOSTS_LIST):

    for host in HOSTS_LIST:

        hostname = ''.join(host)

        hostname = hostname.replace(".", "")

        path_to_graph = RRD_GRAPH_FOLDER_NAME + "/" + hostname + ".png"

        rrd_graph_obj = FileWorker(path_to_graph)

        rrd_graph_status = rrd_graph_obj.check_if_file_exists()

        if rrd_graph_status:

            del rrd_graph_obj

            continue

        else:

            host_db_name = RRD_DB_FOLDER_NAME + "/" + hostname + ".rrd"

            date_time = datetime.datetime.now()
            
            rrdtool.graph(path_to_graph, "-w", "700", "-h", "360", "-a", "PNG", "--slope-mode", "--start", "-86400", "--end", "now",

                          "--font", "WATERMARK:7:Liberation Sans", "--font", "TITLE:15:Liberation Sans",

                          "--font", "AXIS:12:Liberation Sans", "--font", "AXIS:12:Liberation Sans",

                          "--font", "UNIT:12:Liberation Sans", "--font", "LEGEND:12:Liberation Sans",

                          "--title", host, "--watermark", "Generated " + str(date_time),

                          "--vertical-label", "Average rtt", "--lower-limit", "0", "--upper-limit", "999",

                          "--right-axis", "1:0", "--x-grid", "MINUTE:10:HOUR:1:MINUTE:120:0:%R", "--alt-y-grid",

                          "--rigid", "DEF:" + hostname + "=" + host_db_name + ":" + hostname + ":LAST",

                          "HRULE:100#ff0000::dashes=2", "LINE2:" + hostname + "#0000cc:" + hostname,

                          "GPRINT:" + hostname + ":LAST:" + "%6.3lf%s")

            del rrd_graph_obj


def generate_html_monitor_page(MONITOR_FILE, RRD_GRAPH_FOLDER_NAME_HTML, RRD_GRAPH_FOLDER_NAME):

    monitor_file_obj = FileWorker(MONITOR_FILE)

    monitor_file_status = monitor_file_obj.check_if_file_exists()

    if monitor_file_status:

        del monitor_file_obj

    else:

        monitor_file_obj.create_file()

        del monitor_file_obj
        
    for file in os.listdir(RRD_GRAPH_FOLDER_NAME):

        image_path = RRD_GRAPH_FOLDER_NAME_HTML + "/" + file
                    
        GRAPH_LIST.append(image_path)

    page = Environment().from_string(HTML).render(images=GRAPH_LIST)
    
    with open(MONITOR_FILE, 'r+') as mf:

        mf.write(page)


def delete_rrd_db_and_graph(hostname, RRD_DB_FOLDER_NAME, RRD_GRAPH_FOLDER_NAME):

    hostname = ''.join(hostname)

    hostname = hostname.replace(".", "")

    rrd_db_file_path = RRD_DB_FOLDER_NAME + "/" + hostname + ".rrd"

    rrd_graph_file_path =  RRD_GRAPH_FOLDER_NAME + "/" + hostname + ".png"

    os.remove(rrd_db_file_path)

    os.remove(rrd_graph_file_path)


def update_hosts_list_and_files(HOSTS_FILE, HOSTS_LIST):

    host_file_obj = FileWorker(HOSTS_FILE)

    current_hosts_list = host_file_obj.read_file()

    for hostname in current_hosts_list:

        if hostname not in HOSTS_LIST:

           HOSTS_LIST.append(hostname)


    check_if_rrd_db_exists_or_create_it(RRD_DB_FOLDER_NAME, HOSTS_LIST)

    check_if_rrd_graph_exists_or_create_it(RRD_GRAPH_FOLDER_NAME, RRD_DB_FOLDER_NAME, HOSTS_LIST)

    for hostname in HOSTS_LIST:

        if hostname not in current_hosts_list:

            HOSTS_LIST.remove(hostname)

            delete_rrd_db_and_graph(hostname, RRD_DB_FOLDER_NAME, RRD_GRAPH_FOLDER_NAME)

    del host_file_obj


def update_rrd_base(RESPONCE_DATA, RRD_DB_FOLDER_NAME):

        for key, value in RESPONCE_DATA.items():

            hostname = ''.join(key)

            hostname = hostname.replace(".", "")

            path_to_db = RRD_DB_FOLDER_NAME + "/" + hostname + ".rrd"

            rrdtool.update(path_to_db, 'N:' + str(value))


if __name__ == "__main__":

    hosts_file_status, hosts_file_obj = check_hosts_file(HOSTS_FILE)
    
    if hosts_file_status:
        
        collect_hosts(hosts_file_obj)
        
        get_connection_hosts_info(HOSTS_LIST)
        
        check_if_folder_exists_or_create_it(RRD_DB_FOLDER_NAME)

        check_if_folder_exists_or_create_it(RRD_GRAPH_FOLDER_NAME)
        
        check_if_rrd_db_exists_or_create_it(RRD_DB_FOLDER_NAME, HOSTS_LIST)

        check_if_rrd_graph_exists_or_create_it(RRD_GRAPH_FOLDER_NAME, RRD_DB_FOLDER_NAME, HOSTS_LIST)

        generate_html_monitor_page(MONITOR_FILE, RRD_GRAPH_FOLDER_NAME_HTML, RRD_GRAPH_FOLDER_NAME)

        while True:

            update_hosts_list_and_files(HOSTS_FILE, HOSTS_LIST)

            get_connection_hosts_info(HOSTS_LIST)

            update_rrd_base(RESPONCE_DATA, RRD_DB_FOLDER_NAME)

            sleep(SLEEP_TIME)

    else:
        raise SystemExit

    
