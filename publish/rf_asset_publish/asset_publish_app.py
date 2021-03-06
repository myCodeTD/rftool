#Import python modules
import sys, os, re, shutil, random, subprocess, inspect

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#Import GUI
from PySide import QtCore
from PySide import QtGui
from PySide import QtUiTools

from shiboken import wrapInstance

#Import maya commands
import maya.cmds as mc
import maya.mel as mm
from functools import partial

#import rftool commands
# from rftool import publish
from rftool.utils import file_utils
from rftool.utils import path_info
from rftool.utils import maya_utils
from rftool.utils import sg_wrapper
from rftool.utils import sg_process
from rftool.publish.utils import pub_utils
from startup import config

module_path = sys.modules[__name__].__file__
module_dir  = os.path.dirname(module_path)

import maya.OpenMayaUI as mui

# If inside Maya open Maya GUI
def getMayaWindow():
    ptr = mui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QtGui.QWidget)

def show():
    uiName = 'asset_publish_UI'
    deleteUI(uiName)
    myApp = AssetPublish(getMayaWindow())
    # myApp.show()

def deleteUI(ui):
    if mc.window(ui, exists=True):
        mc.deleteUI(ui)
        deleteUI(ui)

class AssetPublish(QtGui.QMainWindow):

    def __init__(self, parent=None):
        #Setup Window
        super(AssetPublish, self).__init__(parent)

        self.runUI()
        self.initial_UI()
        self.init_connect()

    def runUI(self):
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(module_dir + "/ui.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file, self)
        file.close()

        self.ui.show()

    def initial_UI(self):

        try:
            self.asset = path_info.PathInfo()
            self.this_path = self.asset.path
            self.project = self.asset.project
            self.version_name = self.asset.versionNoUser
            self.version = file_utils.find_version(self.this_path)
            self.type_name = self.asset.type
            self.subtype_name = self.asset.subtype
            self.asset_name = self.asset.name
            self.department = self.asset.step
            self.task_name = self.asset.task
            # self.user_name = self.scene.user
            self.src_pub_path = self.asset.entityPath(root='RFPUBL') + '/srcPublish/' + self.version_name
            # self.pub_path = self.asset.entityPath(root='RFPUBL') + '/srcPublish/' + self.version_name
            self.prod_dir = self.asset.entityPath(root='RFPROD')
            self.image_prod = self.asset.entityPath(root='RFPROD') + '/images/' + self.department + '/' + self.version_name
            self.image_publ = self.asset.entityPath(root='RFPUBL') + '/images/' + self.department + '/' + self.version_name
            self.image_path_no_ext = self.image_prod + '/' + self.version_name

            self.movie_prod = self.asset.entityPath(root='RFPROD') + '/movies/' + self.department + '/' + self.version_name
            self.movie_publ = self.asset.entityPath(root='RFPUBL') + '/movies/' + self.department + '/' + self.version_name

            self.thumbnail = ''
            self.movie = ''

            self.get_sg_data()
            self.set_ui_information()
            self.get_thumbnail_version()

        except AttributeError as attrErr :
            print attrErr, ',', self.this_path
            QtGui.QMessageBox.warning(self, 'Warning', 'No Maya Scene Open')

    def init_connect(self):
        ''' connect signals '''
        self.ui.action_add_check_up.triggered.connect(self.add_checkup_lists)
        self.ui.screen_capture_pushButton.clicked.connect(self.screen_capture)
        self.ui.upload_movie_pushButton.clicked.connect(self.upload_movie)
        self.ui.autoCheck_pushButton.clicked.connect(self.auto_check)
        self.ui.review_pushButton.clicked.connect(self.review)

        # self.ui.low_checkBox.toggled.connect(self.check_res)
        # self.ui.med_checkBox.toggled.connect(self.check_res)
        # self.ui.high_checkBox.toggled.connect(self.check_res)

        self.ui.publish_pushButton.clicked.connect(self.publish)

    def set_ui_information(self):
        # hide unused
        # self.ui.res_frame.setVisible(False)
        self.email_name = { 'model': 'model@riffanimation.com', 'rig': 'rig@riffanimation.com', 'texture': 'texture@riffanimation.com', 'shade': 'shade@riffanimation.com' }

        self.main_styleSheet = 'QPushButton {\n    background-color: rgb(100, 200, 0);\n    border-style: inset;\n    border-width: 1px;\n    border-radius: 6px;\n    border-color: rgb(10, 90, 0);\n    font: bold 12px;\n}\nQPushButton:pressed {\n    background-color: rgb(15, 125, 15);\n}'
        self.sub_styleSheet = 'QPushButton {\n    background-color: rgb(255, 100, 0);\n    border-style: inset;\n    border-width: 1px;\n    border-radius: 6px;\n    border-color: rgb(100, 25, 0);\n    font: bold 11px;\n}\nQPushButton:pressed {\n    background-color: rgb(20, 20, 20);\n}'
        self.none_styleSheet = 'QPushButton {\n    background-color: rgb(115, 115, 115);\n    border-style: inset;\n    border-width: 1px;\n    border-radius: 6px;\n    border-color: rgb(100,25, 0);\n    font: bold 11px;\n}\nQPushButton:pressed {\n    background-color: rgb(160, 160, 160);\n}'

        # self.ui.publish_pushButton.setStyleSheet(self.none_styleSheet)
        # self.ui.publish_pushButton.setEnabled(False)
        self.hide_progressBar()
        self.ui.version_lineEdit.setText(self.version_name)
        self.ui.type_lineEdit.setText(self.type_name)
        self.ui.subtype_lineEdit.setText(self.subtype_name)
        self.ui.name_lineEdit.setText(self.asset_name)
        self.ui.department_lineEdit.setText(self.department)
        self.set_tasks_comboBox()

    def set_tasks_comboBox(self):
        activeRow = 0
        for row, task in enumerate(sorted(self.sg_tasks)):
            self.ui.task_comboBox.addItem(task.get('content'))
            self.ui.task_comboBox.setItemData(row, task, QtCore.Qt.UserRole)
            if self.task_name == task.get('content'):
                activeRow = row

        self.ui.task_comboBox.setCurrentIndex(activeRow)

    def get_thumbnail_version(self):
        if os.path.exists(self.image_prod):
            media_list = file_utils.listFile(self.image_prod)
            if media_list :

                for media in media_list:
                    if media.split('.')[-1] in ['mov','avi','mp4']:
                        self.movie = self.asset.entityPath(root='RFPROD') + '/movies/' + media_list
                        break

                        self.set_movie()

                if '.jpg' in media_list[-1]:
                    self.thumbnail = self.image_prod + '/' + media_list[-1]
                    self.set_thumbnail()

    def get_sg_data(self):
        task = str(self.ui.task_comboBox.currentText())

        self.sg_asset = sg_process.get_one_asset(self.project,self.asset_name)
        self.sg_tasks = sg_process.get_tasks_by_step(self.sg_asset,self.department)
        self.sg_task  = sg_process.get_tasks_by_step(self.sg_asset,task)

        if self.sg_task:

            if self.sg_task['sg_status_list'] == 'pub':
                self.trace('Ready for Publish')
                self.ui.publish_pushButton.setStyleSheet(self.main_styleSheet)
                self.ui.publish_pushButton.setEnabled(True)


    def add_checkup_lists(self):
        module_publish = os.path.dirname(module_dir) + '/utils/check_' + self.department + '.py'
        module_publish = module_publish.replace('/','\\')
        subprocess.Popen('explorer /select,"%s"' %(module_publish))

    def screen_capture(self):
        image_path = file_utils.find_next_image_path('%s.jpg' %(self.image_path_no_ext))
        maya_utils.setup_asset_viewport_capture()
        atFrame = '%04d' % mc.currentTime(q=True)
        self.thumbnail = maya_utils.playblast_capture_1k(image_path, atFrame=atFrame)
        print self.thumbnail

        if self.thumbnail:
            self.set_thumbnail()

    def set_thumbnail(self):
        self.ui.thumbnail_label.clear()
        pixmap = QtGui.QPixmap(self.thumbnail)
        pixmap = pixmap.scaled(430, 430, QtCore.Qt.KeepAspectRatio)
        self.ui.thumbnail_label.setPixmap(pixmap)

    def set_movie(self):
        self.ui.movie_lineEdit.setText(self.movie)

    def upload_movie(self):
        workspace = mc.workspace(q=True,dir=True)
        fileName = QtGui.QFileDialog.getOpenFileName(self,"Open Movie", workspace + '/movies', "Movie Files (*.mov *.avi *.mp4)")
        self.movie = self.movie_prod + '.' + fileName[0].split('.')[-1]

        self.show_progressBar()
        i = 0

        while i != 20:
            self.trace('Copying Movie to Server',i)
            i += 1
        
        file_utils.copy(fileName[0], self.movie)

        while i != 100:
            self.trace('Copying Movie to Server',i)
            i += 1

        self.set_movie()
        self.hide_progressBar()
        self.trace('Ready')

    def check_res(self):
        if not self.ui.low_checkBox.isChecked() and not self.ui.med_checkBox.isChecked() and not self.ui.high_checkBox.isChecked() :
            QtGui.QMessageBox.warning(self, 'Warning', 'You can\'t unchecked all resolution checkboxs. Check \'MED\' resolution.')
            self.ui.med_checkBox.setChecked(True)


    def check_task_resolution(self):
        res = []

        if self.ui.med_checkBox.isChecked():
            res.append('md')
        if self.ui.low_checkBox.isChecked():
            res.append('lo')
        if self.ui.high_checkBox.isChecked():
            res.append('hi')

        return res

    def get_email(self):

        self.send_email = ''

        if self.ui.model_checkBox.isChecked():
            self.send_email = self.email_name['model']
        if self.ui.rig_checkBox.isChecked():
            self.send_email = self.email_name['rig']
        if self.ui.texture_checkBox.isChecked():
            self.send_email = self.email_name['texture']
        if self.ui.shade_checkBox.isChecked():
            self.send_email = self.email_name['shade']


    def get_message(self):
        self.message = str(self.ui.message_plainTextEdit.toPlainText())

    def auto_check(self):
        chk_dup = maya_utils.check_duplicate_name()

        if not chk_dup:
            QtGui.QMessageBox.warning(self, 'Warning', 'Duplicated names exist.\nPlease check in outliner and rename them before publish.')
            self.ui.publish_pushButton.setStyleSheet(self.none_styleSheet)
            self.ui.publish_pushButton.setEnabled(False)

        else:
            self.trace('Check OK.')
            self.ui.publish_pushButton.setStyleSheet(self.main_styleSheet)
            self.ui.publish_pushButton.setEnabled(True)

    def trace(self,status,percentage = 0):
        self.ui.status_label.setText(status)
        self.ui.progressBar.setValue(percentage)
        QtGui.QApplication.processEvents()

    def cal_percentage(self,full,fraction,point):
        return point*(fraction/full)

    def show_progressBar(self):
        self.ui.progressBar.setVisible(True)

    def hide_progressBar(self):
        self.ui.progressBar.setVisible(False)

    def review(self):
        version_status = 'rev'
        task_status = 'rev'

        task = str(self.ui.task_comboBox.currentText())
        self.sg_task = sg_process.get_tasks_by_step(self.sg_asset,task)

        self.get_message()

        if self.thumbnail:

            self.show_progressBar()
            i = 0
            j = 0

            task_ent = self.ui.task_comboBox.itemData(self.ui.task_comboBox.currentIndex(), QtCore.Qt.UserRole)
            self.version_name = self.version_name

            self.trace('Create \"%s\" Version on Shotgun' %(self.version_name),25.0)
            pub_utils.create_sg_version(self.project, self.sg_asset, self.version_name, task_ent, version_status ,self.thumbnail, self.message, self.movie)

            self.trace('Update \"Pending for Review\" Status on Shotgun',75.0)
            pub_utils.set_sg_status([task_ent],'rev')

            self.trace('Submit Completed!!',100.0)
            self.hide_progressBar()
            QtGui.QMessageBox.information(self, 'Information', 'Submit Completed!!')

        if not self.thumbnail:
            self.hide_progressBar()
            self.trace('No thumbnail Image')
            QtGui.QMessageBox.warning(self, 'Warning', 'No thumbnail file. Please create one.')

    def publish(self):

        prepub = None
        heropub = None
        sgpub = None

        version_status = 'apr'
        task_status = 'apr'

        self.get_message()

        try:
            sg_version = pub_utils.check_sg_version(self.version_name)

            if sg_version:
                self.show_progressBar()
                i = 0
                j = 0

                prepub = pub_utils.create_asset_pre_publish(self.this_path, self.department, self.task_name)
                self.trace('Export Resource Files',15.0)

                sgpub = pub_utils.set_sg_version(sg_version,version_status)
                self.trace('Update \"%s\" Version' %(self.version_name),25.0)
                

                if self.thumbnail:
                    pub_utils.copy_media_version(self.image_prod,self.image_publ,self.version_name)
                    self.trace('Copy Media to Publish Folder',30.0)
                if self.movie:
                    pub_utils.copy_media_version(self.movie_prod,self.movie_publ,self.version_name)
                    self.trace('Copy Media to Publish Folder',50.0)

                increment = pub_utils.create_increment_work_file(self.this_path)
                self.trace('Increment File to %s' %(increment.split('/')[-1]),75.0)

                self.trace('Update \"Final\" Status on Shotgun',90.0)
                pub_utils.set_sg_status(self.sg_tasks,task_status)

                self.trace('Publish Completed!!',100.0)
                self.hide_progressBar()
                QtGui.QMessageBox.information(self, 'Information', 'Publish Completed!!')

            else:
                answer = QtGui.QMessageBox.question(self, 'Publish', 'No This Version Name Exist!, Do you want to publish now?')

                if self.thumbnail:
                    task_status = 'p_aprv'
                    task_ent = self.ui.task_comboBox.itemData(self.ui.task_comboBox.currentIndex(), QtCore.Qt.UserRole)

                    self.trace('Create \"%s\" Version on Shotgun' %(self.version_name),25.0)
                    pub_utils.create_sg_version(self.project, self.sg_asset, self.version_name, task_ent, version_status ,self.thumbnail, self.message, self.movie)

                    self.trace('Copy Media to Publish Folder',45.0)
                    if self.thumbnail:
                        pub_utils.copy_media_version(self.image_prod,self.image_publ,self.version_name)
                    if self.movie:
                        pub_utils.copy_media_version(self.movie_prod,self.movie_publ,self.version_name)

                    self.trace('Increment File to %s' %(increment.split('/')[-1]), 65.0)
                    increment = pub_utils.create_increment_work_file(self.this_path)

                    self.trace('Update \"Final\" Status on Shotgun',85.0)
                    pub_utils.set_sg_status(self.sg_tasks,task_status)

                    self.trace('Publish Completed!!',100.0)
                    QtGui.QMessageBox.information(self, 'Information', 'Publish Completed!!')
                    self.hide_progressBar()

                else:
                    self.trace('No thumbnail Image')
                    QtGui.QMessageBox.warning(self, 'Warning', 'No thumbnail file. Please click on \"Screen Capture\" and publish again.')
                    self.hide_progressBar()
                    
        except TypeError as exc:

            if not sg_wrapper.get_version_entity(self.version_name):
                QtGui.QMessageBox.information(self, 'Error', 'No \"%s\" Exists on shotgun.\nPlease match your version' %(self.version_name))

            else:
                print 'TypeError : ' , exc
                print 'Resource Files' , prepub
                print 'Lib Hero' , heropub
                print 'Shotgun Update' , sgpub
                self.hide_progressBar()
                QtGui.QMessageBox.information(self, 'Error', 'Please Check in Script Editor.\nTypeError : %s' %(exc))




# class AddThumbnailVersion(QtGui.QMainWindow):
#      """docstring for AddThumbnailVersion"""
#     def __init__(self, parent=None):
#         super(AddThumbnailVersion, self).__init__(parent)

#         self.runUI()
         
#     def runUI(self):
#         loader = QtUiTools.QUiLoader()
#         file = QtCore.QFile(module_dir + "/add.ui")
#         file.open(QtCore.QFile.ReadOnly)
#         self.ui = loader.load(file, self)
#         file.close()

#         self.ui.show()

#     def initConnect(self):

#         self.ui.movie_lineEdit.installEventFilter()
#         self.ui.image_lineEdit.installEventFilter()

#         self.ui.ok_pushButton.clicked.connect(self.close_add)

#     def eventFilter(self, source, event):

#         if (event.type() == QtCore.QEvent.Drop):

#             if event.mimeData().hasUrls():
#                 input_text = str(event.mimeData().hasUrls())
#                 source.setText(input_text)

#     def closeAdd(self):

#         self.close()