import os

try: 
    import maya.cmds as mc
    import maya.mel as mm
    isMaya = True

except ImportError: 
    isMaya = False

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# if isMaya: 
#     for path in os.environ['MAYA_PLUG_IN_PATH'].split(';'):
#         if os.path.exists(path + '/AbcImport.mll'):
#             if not mc.pluginInfo('AbcImport.mll', q=True, l=True):
#                 mc.loadPlugin(path + '/AbcImport.mll')

#         if os.path.exists(path + '/AbcExport.mll'):
#             if not mc.pluginInfo('AbcExport.mll', q=True, l=True):
#                 mc.loadPlugin(path + '/AbcExport.mll')

#         if os.path.exists(path + '/gpuCache.mll'):
#             if not mc.pluginInfo('gpuCache.mll', q=True, l=True):
#                 mc.loadPlugin(path + '/gpuCache.mll')

def get_path():
    return mc.file(q=True, loc=True)

def setup_asset_viewport_capture():
    mc.grid(toggle=0)
    perspPanel = mc.getPanel( withLabel='Persp View')
    mc.modelEditor(perspPanel,e=True,hud=False)
    mc.setAttr("defaultResolution.width",1024)
    mc.setAttr("defaultResolution.height",1024)

def setup_scene_viewport_playblast():
    mc.grid(toggle=0)
    perspPanel = mc.getPanel( withLabel='Persp View')
    mc.modelEditor(perspPanel,e=True,hud=False)
    mc.setAttr("defaultResolution.width",1024)
    mc.setAttr("defaultResolution.height",1024)

def playblast_capture_1k(image_path, atFrame=None, w=1024, h=1024):
    file_extention = image_path.split('.')[-1]
    index = int(image_path.split('.')[-2])
    image_no_extention = image_path.split('.')[0]
    print image_no_extention

    if not atFrame:
        atFrame = index

    result = mc.playblast(format='image',
                    filename=image_no_extention,
                    st=atFrame,
                    et=atFrame,
                    sequenceTime=0,
                    clearCache=1,
                    viewer=0,
                    showOrnaments=1,
                    fp=4,
                    percent=100,
                    compression=file_extention,
                    quality=100,
                    widthHeight=[w, h])

    if result:
        print 'result', result
        # result = result.replace('####',image_path.split('.')[-2])
        targetFile = result.replace('####',image_path.split('.')[-2]).replace('\\', '/')
        tmpFile = result.replace('####',atFrame).replace('\\', '/')
        print atFrame
        print tmpFile
        print targetFile

        if os.path.exists(tmpFile):
            os.rename(tmpFile, targetFile)

        print 'result', result

        return targetFile

def playblast_avi(mov_path,start,end,resolution,width=960,height=540):
    # playblast  -fmt "avi" -startTime 301 -endTime 325 -sequenceTime 1 -forceOverwrite -filename "movies/s0030.avi" -clearCache 1 -showOrnaments 0 -percent 100 -wh 1024 778 -offScreen -viewer 0 -useTraxSounds -compression "none" -quality 70;
    image_no_extention = mov_path.split('.')[0]
    file_extention = mov_path.split('.')[-1]

    if file_extention == 'avi':
        result = mc.playblast(format=file_extention,
                        filename=mov_path,
                        st=start,
                        et=end,
                        sequenceTime=1,
                        forceOverwrite=True,
                        clearCache=1,
                        viewer=0,
                        showOrnaments=1,
                        percent=100,
                        compression="none",
                        quality=resolution,
                        widthHeight=[width,height],
                        useTraxSounds=True)

    if file_extention == 'jpg':
        result = mc.playblast(format='image',
                    filename=image_no_extention,
                    st=start,
                    et=start,
                    sequenceTime=0,
                    clearCache=1,
                    viewer=0,
                    showOrnaments=1,
                    fp=4,
                    percent=100,
                    compression=file_extention,
                    quality=100,
                    widthHeight=[width,height])
        result = result.replace('####','%04d' %(start))

    return result


def capture_screen(dst, format, st, sequencer, w, h) : 
    outputFile = dst.split('.')[0]
    extension = dst.split('.')[-1]

    start = st
    end = start

    result = mc.playblast( format= 'iff' ,
                            filename= outputFile,
                            st=start ,
                            et=end ,
                            forceOverwrite=True ,
                            sequenceTime=sequencer ,
                            clearCache=1 ,
                            viewer= 0 ,
                            showOrnaments=1 ,
                            fp=4 ,
                            widthHeight= [w,h] ,
                            percent=100 ,
                            compression= format ,
                            offScreen=True ,
                            quality=70
                            )


    if result : 
        padding = '%04d' % start 
        output = result.replace('####', padding)
        if os.path.exists(dst) : 
            os.remove(dst)
        os.rename(output, dst)

        return dst

def correct_cam(shotName):
    cam_name = shotName + '_cam'
    st = 0
    et = 0

    if mc.shot(shotName, q=True ,currentCamera=True) == cam_name:
        st = mc.getAttr('%s.startFrame' %(shotName))
        et = mc.getAttr('%s.endFrame' %(shotName))

    return cam_name,st,et

def setup_scene_viewport_playblast(shotName):
    mc.grid(toggle=0)

    mc.setAttr("defaultResolution.width",960)
    mc.setAttr("defaultResolution.height",540)

    if mc.objExists(shotName):
        mc.setAttr('%s_camShape.displayGateMask' %(shotName), True)
        mc.setAttr('%s_camShape.displayResolution' %(shotName), True)
        mc.setAttr('%s_camShape.displayGateMaskOpacity' %(shotName), 1)
        mc.setAttr('%s_camShape.displayGateMaskColor' %(shotName), 0, 0, 0, type='double3')
        mc.setAttr('%s_camShape.overscan' %(shotName),1.0)

def get_current_shot():
    return mc.sequenceManager(q=True,currentShot=True)

def get_current_frame_no(shotName):
    cam_name, sf, ef = correct_cam(shotName)
    ft = (ef - sf) + 1.0
    cf = mc.currentTime(q=True)
    ct = (cf - sf) + 1.0

    return '%d/%d' %(ct,ft)

def get_current_frame(shotName):
    cam_name, sf, ef = correct_cam(shotName)
    cf = mc.currentTime(q=True)

    return '%d/%d' %(cf,ef)

def set_first_frame(shotName):
    st = mc.getAttr('%s.startFrame' %(shotName))
    mc.currentTime(st)
    mc.sequenceManager(currentTime=st)


def HUDClear():
    for hud in mc.headsUpDisplay(listHeadsUpDisplays=True):
        mc.headsUpDisplay(hud,edit=True, visible=False)
        mc.headsUpDisplay(hud,refresh=True)

def HUDPlayblast(user,versionName):

    HUDClear()

    hud_lists = [ 'HUDUsername', 'HUDCurrentTime', 'HUDFilename', 'HUDCurrentShot', 'HUDCurrentFrame', 'HUDOverAll' ]

    # [i for i, j in zip(a, b) if i == j]

    # Left-Bottom
    mc.headsUpDisplay( rp=(5, 3) )
    if not mc.headsUpDisplay('HUDUsername', exists=True):
        mc.headsUpDisplay('HUDUsername', section=5, block=3, label='User : ', command='sp_app.path_info.PathInfo().user', attachToRefresh=True, blockAlignment='left')
    if mc.headsUpDisplay('HUDUsername',exists = True):
        mc.headsUpDisplay('HUDUsername', edit=True, section=5, block=3, label='User : ', command='sp_app.path_info.PathInfo().user', attachToRefresh=True, blockAlignment='left')
    mc.headsUpDisplay( rp=(5, 2) )
    if not mc.headsUpDisplay('HUDCurrentTime',exists = True):
        mc.headsUpDisplay('HUDCurrentTime', section=5, block=2, label='Date/Time : ', command='sp_app.file_utils.get_now_time()', attachToRefresh=True, blockAlignment='left')
    if mc.headsUpDisplay('HUDCurrentTime',exists = True):
        mc.headsUpDisplay('HUDCurrentTime', edit=True, section=5, block=2, label='Date/Time : ', command='sp_app.file_utils.get_now_time()', attachToRefresh=True, blockAlignment='left')
    mc.headsUpDisplay( rp=(5, 1) )
    if not mc.headsUpDisplay('HUDFilename',exists = True):
        mc.headsUpDisplay('HUDFilename', section=5, block=1, label='Filename : ', command='sp_app.path_info.PathInfo().versionName', attachToRefresh=True, blockAlignment='left')
    if mc.headsUpDisplay('HUDFilename',exists = True):
        mc.headsUpDisplay('HUDFilename', edit=True, section=5, block=1, label='Filename : ', command='sp_app.path_info.PathInfo().versionName', attachToRefresh=True, blockAlignment='left')

    # Center-Bottom
    mc.headsUpDisplay( rp=(7, 2) )
    if not mc.headsUpDisplay('HUDCurrentShot',exists = True):
        mc.headsUpDisplay('HUDCurrentShot', section=7, block=2, label='Cam : ', command='sp_app.maya_utils.get_current_shot()', attachToRefresh=True, blockAlignment='center', dataFontSize='large')
    if mc.headsUpDisplay('HUDCurrentShot',exists = True):
        mc.headsUpDisplay('HUDCurrentShot', edit=True, section=7, block=2, label='Cam : ', command='sp_app.maya_utils.get_current_shot()', attachToRefresh=True, blockAlignment='center', dataFontSize='large')
    mc.headsUpDisplay( rp=(7, 1) )
    if not mc.headsUpDisplay('HUDCurrentFrame',exists = True):
        mc.headsUpDisplay('HUDCurrentFrame', section=7, block=1, label='Info : ', command='sp_app.maya_utils.get_current_frame_no(sp_app.maya_utils.get_current_shot())', attachToRefresh=True, blockAlignment='center', dataFontSize='large')
    if mc.headsUpDisplay('HUDCurrentFrame',exists = True):
        mc.headsUpDisplay('HUDCurrentFrame', edit=True, section=7, block=1, label='Info : ', command='sp_app.maya_utils.get_current_frame_no(sp_app.maya_utils.get_current_shot())', attachToRefresh=True, blockAlignment='center', dataFontSize='large')

    # Right-Bottom
    mc.headsUpDisplay( rp=(9, 2) )
    if mc.headsUpDisplay('HUDFocalLength',exists = True):
        mc.headsUpDisplay('HUDFocalLength', edit=True, section=9, block=2, attachToRefresh=True, blockAlignment='right')
    mc.headsUpDisplay( rp=(9, 1) )
    if not mc.headsUpDisplay('HUDOverAll',exists = True):
        mc.headsUpDisplay('HUDOverAll', section=9, block=1, label='Over all : ', command='sp_app.maya_utils.get_current_frame(sp_app.maya_utils.get_current_shot())', attachToRefresh=True, blockAlignment='right', dataFontSize='large')
    if mc.headsUpDisplay('HUDOverAll',exists = True):
        mc.headsUpDisplay('HUDOverAll', edit=True, section=9, block=1, label='Over all : ', command='sp_app.maya_utils.get_current_frame(sp_app.maya_utils.get_current_shot())', attachToRefresh=True, blockAlignment='right', dataFontSize='large')


# def create_rig_grp(res='md', ctrl=False):
#     plys = mc.ls(sl=True,l=True)

#     if not mc.objExists('Geo_Grp'):
#         geo_grp = mc.group(em=True,name='Geo_Grp')
#         still_grp = mc.group(em=True,name='Still_Grp')
#         offset_grp = mc.group(em=True,name='Offset_Grp')
#         rig_grp = mc.group(em=True,name='Rig_Grp')

#         if ctrl:
#             ctrl_grp = mc.group(em=True,name='Ctrl_Grp')
#             mc.parent(ctrl_grp,rig_grp)
#             ctrl_grp = mc.group(em=True,name='Placement_Ctrl')

#         mc.parent(geo_grp,rig_grp)
#         mc.parent(still_grp,rig_grp)
#         mc.parent(offset_grp,rig_grp)

#         md_geo_grp = mc.group(em=True,name='Md_Geo_Grp')
#         mc.parent(md_geo_grp,geo_grp)
#         hi_geo_grp = mc.group(em=True,name='Hi_Geo_Grp')
#         mc.parent(hi_geo_grp,geo_grp)
#         lo_geo_grp = mc.group(em=True,name='Lo_Geo_Grp')
#         mc.parent(lo_geo_grp,geo_grp)

#     if plys:
#         if res == 'md':
#             mc.parent(plys, 'Md_Geo_Grp')
#         if res == 'lo':
#             mc.parent(plys, 'Lo_Geo_Grp')
#         if res == 'hi':
#             mc.parent(plys, 'Hi_Geo_Grp')

#     for ply in plys:
#         oldname = ply.split('|')[-1]
#         newname = '_'.join([res,oldname])
#         mc.rename(oldname,newname)

# def create_rig_grp(objs=None, res='md', ctrl=True):
#     from rftool.rig.utils import main_group
#     if not objs:
#         objs = mc.ls(sl=True)

#     rigGrp = main_group.MainGroup('rig')

#     if not ctrl:
#         mc.delete(rigGrp.Place_Ctrl)

#     if objs:
#         if res == 'md':
#             mc.parent(objs, rigGrp.Geo_Md)
#         if res == 'hi':
#             mc.parent(objs, rigGrp.Geo_Hi)
#         if res == 'lo':
#             mc.parent(objs, rigGrp.Geo_Lo)
#         if res == 'pr':
#             mc.parent(objs, rigGrp.Geo_Pr)

#     return rigGrp

def create_rig_grp(objs=None, res='md', ctrl=True): 
    from rftool.rig.utils import mainCtrl
    reload(mainCtrl)
    if not objs:
        objs = mc.ls(sl=True)

    rigGrp = mainCtrl.rigMain()
    return rigGrp



def create_gpu_cache(objName='',gpuDirname='',gpuBasename=''):
    # gpuCache -startTime 1 -endTime 1 -optimize -optimizationThreshold 40000 -writeMaterials -dataFormat ogawa -directory "C:/Users/vanef/Dropbox/media_server/project/asset/prop/general/glass/prePublish" -fileName "glass_gpu" Md_Geo_Grp;
    return mc.gpuCache(objName,startTime=1,endTime=1,optimize=True,optimizationThreshold=40000,writeMaterials=True,dataFormat="ogawa",fileName=gpuBasename,directory=gpuDirname)

def create_abc_cache(objLongName='',abcPath=''):
    # AbcExport -j "-frameRange 1 1 -uvWrite -worldSpace -writeVisibility -dataFormat ogawa -root |Rig_Grp|Geo_Grp|Md_Geo_Grp -file C:/Users/vanef/Dropbox/media_server/project/asset/prop/general/glass/cache/glass_abc.abc";
    return mc.AbcExport(j="-frameRange 1 1 -uvWrite -worldSpace -writeVisibility -dataFormat ogawa -root %s -file %s" %(objLongName,abcPath))

def check_duplicate_name():

    if mc.objExists('rig_grp'):
        mc.select('rig_grp', hi=True )
        lists = mc.ls(sl=True,type='transform')

        mc.select(clear=True)
        unDup = []

        for list in lists:
            #print list.split('|')[-1]
            if not list.split('|')[-1] in unDup:
                unDup.append(list.split('|')[-1])

            else:
                mc.select(('*%s*') %(list.split('|')[-1]), add=True)

        if mc.ls(sl=True):
            return False

        else:
            return True

# def HUDPlayblast():
#     from rftool.utils import path_info
#     path = path_info.PathInfo()
#     filename = path.versionName

#     mc.headsUpDisplay('HUDFilename', section=1, block=5, label='Filename : ', command='path.versionName')
#     mc.headsUpDisplay('HUDFilename', edit=True, visability=True)

def create_reference(assetName, path):
    if os.path.exists(path):
        namespace = get_namespace('%s_001' % assetName)
        result = mc.file(path, r=True, ns=namespace)
        return namespace

def import_reference(assetName, path):
    if os.path.exists(path):
        namespace = get_namespace('%s_001' % assetName)
        result = mc.file(path, i=True, ns=namespace)
        return namespace

def create_asm_reference(assetName, path):
    import asm_utils
    if os.path.exists(path):
        namespace = get_namespace('%s_001' % assetName)
        arNode = asm_utils.createARNode()
        asm_utils.setARDefinitionPath(arNode, path)
        asm_utils.setARNamespace(arNode, namespace)
        result = mc.rename(arNode, '%s_AR' % assetName)

        return result

def duplicate_reference(path):
    namespace = mc.file(path, q=True, namespace=True)
    newNamespace = get_namespace(namespace)
    result = mc.file(path, r=True, ns=newNamespace)
    return newNamespace

def open_file(path):
    if os.path.exists(path):
        mc.file(path,f=True,o=True)

def import_file(assetName,path):
    if os.path.exists(path):
        namespace = get_namespace('%s_001' % assetName)
        mc.file(path,i=True,ns=namespace)
        # mc.file -import -type "mayaAscii"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace "stoolA_rig_md" -options "v=0;p=17;f=0"  -pr "C:/Users/User/Dropbox/publ_server/project/asset/setDress/furniture/stoolA/lib/stoolA_rig_md.ma";


def get_namespace(namespace):
    # asset_001
    if not mc.namespace(ex=namespace):
        return namespace

    else:
        padding = namespace.split('_')[-1]
        if padding.isdigit():
            incrementPadding = '%03d' % (int(padding) + 1)
            newNamespace = namespace.replace(padding, incrementPadding)

        else:
            newNamespace = '%s_001' % namespace

        return get_namespace(newNamespace)

def export_selection(exportPath, obj):
    exportResult = False

    if not os.path.exists(exportPath):
        mtime = 0

    else:
        mtime = os.path.getmtime(exportPath)

    mc.select(obj)
    result = mc.file(exportPath, f=True, es=True, type='mayaAscii')

    if os.path.exists(exportPath):
        if not mtime == os.path.getmtime(exportPath):
            exportResult = True

    if exportResult:
        return result


def export_gpu(objs, dstDir, filename, time='still'):
    import asm_utils
    gpuPath = '%s/%s.abc' % (dstDir, filename)
    exportResult = False

    if not os.path.exists(gpuPath):
        mtime = 0
    else:
        mtime = os.path.getmtime(gpuPath)

    asm_utils.exportGPUCacheGrp(objs, dstDir, filename, time=time)

    if os.path.exists(gpuPath):
        if not mtime == os.path.getmtime(gpuPath):
            exportResult = True

    if exportResult:
        return gpuPath


def export_geo(objs, dstDir, filename, removeRig=True):
    import pipeline_utils 
    geoPath = '%s/%s' % (dstDir, filename)
    exportResult = False

    if not os.path.exists(geoPath):
        mtime = 0
    else:
        mtime = os.path.getmtime(geoPath)

    if removeRig: 
        remove_rig(objs, pipeline_utils.config.ctrlGrp)

    result = mc.file(geoPath, f=True, es=True, type='mayaAscii')

    if os.path.exists(geoPath):
        if not mtime == os.path.getmtime(geoPath):
            exportResult = True

    if exportResult:
        return geoPath


def shiftKey(type = 'default', frameRange = [1, 10000], frame = 0) : 
    """ shift key frame, shift all use default mode """ 
    if type == 'default' : 
        mm.eval('selectKey  -t (":") `ls -dag`;')

    if type == 'start' : 
        mm.eval('selectKey -t ("%s:") `ls -dag`;' % frameRange[0])

    if type == 'range' : 
        mm.eval('selectKey  -t ("%s:%s") `ls -dag`;' % (frameRange[0], frameRange[1]))

    mc.keyframe(e = True, iub = 0, an = 'keys', r = True, o = 'over', tc = frame)


def shiftShot(shotName, frame=0): 
    """ shift individual shot """ 
    sequenceStartFrame = mc.getAttr('%s.sequenceStartFrame' % shotName)
    sequenceEndFrame = mc.getAttr('%s.sequenceEndFrame' % shotName)
    startFrame = mc.getAttr('%s.startFrame' % shotName)
    endFrame = mc.getAttr('%s.endFrame' % shotName)

    mc.setAttr('%s.sequenceStartFrame' % shotName, sequenceStartFrame + frame)
    mc.setAttr('%s.startFrame' % shotName, startFrame + frame)

    mc.setAttr('%s.sequenceEndFrame' % shotName, sequenceEndFrame + frame)
    mc.setAttr('%s.endFrame' % shotName, endFrame + frame)


def shiftSequencer(frame=0, mute=False): 
    """ shift the whole time line """ 
    shots = mc.ls(type='shot')
    infoDict = dict()

    if shots: 
        for shot in shots: 
            sequenceStartFrame = mc.getAttr('%s.sequenceStartFrame' % shot)

            if not sequenceStartFrame in infoDict.keys(): 
                infoDict.update({sequenceStartFrame: [shot]})
            else: 
                infoDict[sequenceStartFrame].append(shot)

        # positive move from last shot
        if frame > 0: 
            shotDict = sorted(infoDict.iteritems())[::-1]

        if frame < 0: 
            shotDict = sorted(infoDict.iteritems())
        
        for key, shots in shotDict: 
            for shotName in shots: 
                shiftShot(shotName, frame=frame)
                mc.shot(shotName, e=True, mute=mute)


def getTextureFile() : 
    """ get texture files in the scene """ 
    fileNodes = mc.ls(type = 'file')
    files = []

    if fileNodes : 
        for each in fileNodes : 
            fileTexture = mc.getAttr('%s.fileTextureName' % each)

            fileStatus = False 
            if os.path.exists(fileTexture) : 
                fileStatus = True 

            files.append((fileTexture, fileStatus))

    return files


def getAssemblyFiles() : 
    """ get assembly node files """ 
    sels = mc.ls(type = 'assemblyReference')
    copyFiles = []

    if sels : 
        for each in sels : 
            ad = mc.getAttr('%s.definition' % each)
            
            if ad : 
                fileStatus = False

                if os.path.exists(ad) : 
                    fileStatus = True
                    
                copyFiles.append((ad, fileStatus))

            datas = listRepIndex(each, 'data')
            
            if datas : 
                for each in datas : 
                    fileStatus = False
                    if os.path.exists(each) : 
                        fileStatus = True
                        
                    copyFiles.append((each, fileStatus))

    return copyFiles


def listRepIndex(assemblyNode, listType = 'name') : 
    lists = mc.assembly(assemblyNode, q = True, listRepresentations = True)

    if listType == 'name' : 
        return lists 

    labels = []
    datas = []

    if lists : 
        for i in range(len(lists)) : 
            label = mc.getAttr('%s.representations[%s].repLabel' % (assemblyNode, i))
            data = mc.getAttr('%s.representations[%s].repData' % (assemblyNode, i))
            labels.append(label)
            datas.append(data)

    if listType == 'label' : 
        return labels 

    if listType == 'data' : 
        return datas


def getMayaSceneAssets(mayaFile, mayaVersion, console=False) : 
    """ get maya assets """ 
    import pipeline_utils

    pyCommand = '%s/core/maya/rftool/utils/get_asset_list.py' % os.getenv('RFSCRIPT')
    pipeline_utils.runMayaPy(pyCommand, mayaVersion, console, mayaFile)

    tmpFile = 'mayaAssetList.txt'
    tmpdir = os.getenv('TMPDIR')
    if not tmpdir: 
        tmpdir = os.getenv('TMP')

    tmpPath = '%s/%s' % (tmpdir, tmpFile)

    if os.path.exists(tmpPath) : 
        f = open(tmpPath, 'r')
        data = f.read()
        f.close()

        result = eval(data)
        os.remove(tmpPath)

        return result 


def exportGPUCacheGrp(exportGrp, exportPath, abcName, time = 'still') : 
    startFrame = 1.0
    endFrame = 1.0

    if time == 'still' : 
        currentFrame = mc.currentTime(q = True)
        startFrame = currentFrame
        endFrame = currentFrame 

    if time == 'animation' : 
        startFrame = mc.playbackOptions(q = True, min = True)
        endFrame = mc.playbackOptions(q = True, max = True)

    # export objs 
    if mc.objExists(exportGrp) : 
        mc.select(exportGrp) 
        result = mc.gpuCache(exportGrp, 
                                startTime = startFrame, 
                                endTime = endFrame, 
                                optimize = True, 
                                optimizationThreshold = 40000, 
                                writeMaterials = True, 
                                dataFormat = 'ogawa', 
                                directory = exportPath, 
                                fileName = abcName, 
                                saveMultipleFiles = False
                                )

        gpupath = '%s/%s.abc' % (exportPath,abcName)

        return result 


def find_same_poly(sel = True) : 
    # find similar polygon by count faces
    sels = mc.ls(sl = True)

    if sels : 
        numFace = mc.polyEvaluate(sels[0], f = True, fmt = True)

        matchPoly = []
        matchPoly.append(sels[0])

        mc.select(cl = True)
        allPlys = mc.ls(type = 'mesh', l = True)

        for each in allPlys : 
            transform = mc.listRelatives(each, p = True, f = True)[0]
            currentFaceCount = mc.polyEvaluate(each, f = True, fmt = True)
            
            if currentFaceCount == numFace : 
                matchPoly.append(transform)
                
        if sel : 
            mc.select(matchPoly)

        return matchPoly


def find_same_poly2(obj) : 
    # find similar polygon by count faces

    numFace = mc.polyEvaluate(obj, f = True, fmt = True)

    matchPoly = []
    matchPoly.append(obj)

    mc.select(cl = True)
    allPlys = mc.ls(type = 'mesh', l = True)

    for each in allPlys : 
        transform = mc.listRelatives(each, p = True, f = True)[0]
        currentFaceCount = mc.polyEvaluate(each, f = True, fmt = True)
        
        if currentFaceCount == numFace : 
            if not transform in matchPoly : 
                matchPoly.append(transform)

    return matchPoly

def remove_rig(rigGrp, ctrlGrp): 
    """ remove rig from given rigGrp """ 
    childs = mc.listRelatives(rigGrp)
    removeObj = [a for a in childs if ctrlGrp in a]

    # show transform 
    show_hide_transform([rigGrp], state=True)

    if removeObj: 
        mc.delete(removeObj)


def show_hide_transform(objs, attrs=['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'], state=True): 
    lock = not state
    for obj in objs: 
        for attr in attrs: 
            mc.setAttr('%s.%s' %(obj, attr), l=lock, cb=state)
            mc.setAttr('%s.%s' %(obj, attr), k=state)



def remove_plugins(): 
    unknownPlugins = mc.unknownPlugin(q=True, list=True)

    if unknownPlugins: 
        for unknownPlugin in unknownPlugins: 
            mc.unknownPlugin(unknownPlugin, remove=True)

        logger.info('Remove %s unknownPlugins' % len(unknownPlugins))
        return 
    logger.info('No unknownPlugins')



def get_ref_path(obj) : 
    return mc.referenceQuery(obj, f = True)


def get_node_namespace(obj) : 
    path = get_ref_path(obj) 
    return mc.file(path, q = True, namespace = True)


def list_top_parent(obj): 
    parents = mc.listRelatives(obj, p=True)
    # take first parent in the list 
    if parents: 
        return list_top_parent(parents[0])
    else: 
        return obj


def find_ply(transform, f=False): 
    """ find polygon under transform """ 
    childs = mc.listRelatives(transform, ad=True, f=True)

    if childs: 
        meshes = list(set([mc.listRelatives(a, p=True, f=f)[0] for a in childs if mc.objectType(a, isType='mesh')]))
        return meshes


def add_prefix(transform, prefix, remove='', hi=True): 
    """ rename prefix """ 
    mc.select(transform, hi=True)
    hierarchy = mc.ls(sl=True, l=True)

    for node in hierarchy[::-1]: 
        if mc.objectType(node, isType='transform'): 
            shortName = node.split('|')[-1]
            if remove: 
                shortName = shortName.replace(remove, '')
            newName = '%s%s' % (prefix, shortName)
            mc.rename(node, newName) 

    mc.select(cl=True)



