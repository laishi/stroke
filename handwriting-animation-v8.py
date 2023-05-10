import bpy
import os
import json
import math
import random
import mathutils

import wave
import codecs
import struct




class GPWriting:
    def __init__(self, greasePencileName=None):
        if greasePencileName:
            self.gp = bpy.data.grease_pencils[greasePencileName]
        else:
            self.gp = bpy.context.active_object.data        
        self.strokeData = []
        self.audioStart = []
        self.audioDuration = []
        self.audioFrames = []
        
        self.penConfig = {
            'penName': 'GPDrawing',
            'penFrames': [],
            'penLocation': [],
            'penColor': [],
            'speed': 1,
            'mixColor': 0.0,
            'penPath': 'C:\\Users\\laish\\SurfaceStudio\\Assets\\Brush\\Penkuzhi02.png'
        }
        
        self.strokeSpaceFrames = round(10 * self.penConfig['speed'])
        
        self.state = self.gp.layers[0].hide
        if self.state:
            self.initWrite()
        else:
            self.getgpdata()
            self.strokeWriting()
            self.penDrawing()
            self.penPlay()
            self.getAudioFrame()
        self.centerView()
            

        
    def getgpdata(self):
        strokeData = []
        gp_frame = self.gp.layers[0].frames[0]
        gp_strokes = gp_frame.strokes
        for i, stroke in enumerate(gp_strokes): 
            sd = []           
            for j,point in enumerate(stroke.points):
                pointData = {}
                x, y, z = point.co
                pointData['id'] = i
                pointData['co'] = [x, y, z]
                pointData['time'] = point.time
#                pointData['co'] = [round(x,2), round(y,2), round(z,2)]
#                pointData['time'] = round(point.time, 2)
                pointData['frame'] = int(point.time * bpy.context.scene.render.fps * self.penConfig['speed'])
                pointData['pressure'] = point.pressure
                pointData['strength'] = point.strength
                pointData['uv_rotation'] = point.uv_rotation
                pointData['vertex_color'] = list(point.vertex_color[:])
                sd.append(pointData)
            strokeData.append(sd)        
        self.strokeData = strokeData 
        return strokeData    
    
    def saveStrokeData(self, path=r"C:\Users\laish\SurfaceStudio\Work\Blender\DB\love.json"):
        try:
            with open(path, "w") as file:
                json.dump(self.strokeData, file)
                print(f'Saved stroke data to: {path}')
        except Exception as e:
            print(f"An error occurred while saving stroke data: {str(e)}")
            
            

            
    def getStrokeAttr(self, attrName):
        strokesAttr = []
        for strokes in self.strokeData:
            strokeAttr = []
            prev_frame  = 0
            for point in strokes:                
                strokeAttr.append(point[attrName])
            strokesAttr.append(strokeAttr)     
        
        if attrName == 'frame':
            framesAttr = []
            for index in range(len(strokesAttr)):
                frames = strokesAttr[index]
                prev_frame = 0
                for i in range(len(frames)):
                    if frames[i] == 0:
                        frames[i] = prev_frame
                    else:
                        prev_frame = frames[i]
                strokesAttr[index] = frames
                framesAttr.append(frames)
            strokesAttr = framesAttr
                        
        return strokesAttr
        

    def sortFrames(self):
        strokeFrames = self.getStrokeAttr('frame')       

        endFrame = 0
        for i in range(len(strokeFrames)):            
            strokeFrame = []            
            for j in range(len(strokeFrames[i])):
                if i > 0:
                    sortFrame = endFrame + self.strokeSpaceFrames
                    strokeFrames[i][j] += sortFrame
                    strokeFrame.append(strokeFrames[i][j])
                else:
                    strokeFrame.append(strokeFrames[i][j])
            endFrame = strokeFrame[-1]
            strokeFrames[i] = strokeFrame
        return strokeFrames
    
    
    def deduplicationByFrames(self, attrName = 'pressure'):
        strokePressure = self.getStrokeAttr(attrName)
        srokeFrames = self.sortFrames()
        
        newStrokePressure = []
        for i in range(len(srokeFrames)):
          sp = []
          sf = []
          
          for j in range(len(srokeFrames[i])):
            
            if j < len(srokeFrames[i])-1:
              # print(srokeFrames[i][j+1])
              if srokeFrames[i][j] != srokeFrames[i][j+1]:
                sp.append(strokePressure[i][j])
                sf.append(srokeFrames[i][j])
            else:
              sp.append(strokePressure[i][j])
              sf.append(srokeFrames[i][j])
          newStrokePressure.append(sp)
        return newStrokePressure



    def getAudioFrame(self):        
        audioFrames = self.sortFrames()
        
        for i in range(len(audioFrames)):
            first_elem = audioFrames[i][0]
            last_elem = audioFrames[i][-1]
            self.audioFrames.append([first_elem, last_elem])
        
    def strokeWriting(self):        
        strokeFrames = self.sortFrames()
        self.strokeData
        for idx, frames in enumerate(strokeFrames):
            stroke = self.strokeData[idx]
            layer_name = 'stroke' + str(idx+1)
            new_layer = self.gp.layers.new(layer_name)
            for i in range(len(frames)):    
                curentFrameNumber = frames[i]
                 
                if i>0 and new_layer.frames[-1].frame_number == curentFrameNumber:
                    new_layer.frames.remove(new_layer.frames[-1])      

                new_frame = new_layer.frames.new(curentFrameNumber)
                new_stroke = new_frame.strokes.new()
                points = stroke[:i+1]                
                new_stroke.points.add(len(points))
                new_stroke.line_width = 100
                for n,pt in enumerate(points):
                    new_stroke.points[n].co = pt['co']
                    new_stroke.points[n].pressure = pt['pressure']
                    new_stroke.points[n].strength = pt['strength']
                    new_stroke.points[n].uv_rotation = pt['uv_rotation']
                    new_stroke.points[n].vertex_color = pt['vertex_color']

                self.penConfig['penFrames'].append(curentFrameNumber)
                self.penConfig['penLocation'].append(stroke[i]['co'])
                self.penConfig['penColor'].append(stroke[i]['vertex_color'])

                
        self.penConfig['penFrames'].append(self.penConfig['penFrames'][-1])
        self.penConfig['penLocation'].append([0,0,0])
        
        self.gp.layers.active_index = 0
        self.gp.layers[0].hide = True
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = self.penConfig['penFrames'][-1]
            
    def createGP(self, GPName=None):
        if GPName is None:
            GPName = self.penConfig['penName']
        gpencil_data = bpy.data.grease_pencils.new(GPName)
        gpencil = bpy.data.objects.new(gpencil_data.name, gpencil_data)
        bpy.context.collection.objects.link(gpencil)
        
        matName = GPName + 'Mat'
        if matName in bpy.data.materials.keys():
            gpmat = bpy.data.materials[matName]
            gpencil.data.materials.append(gpmat)
        else:
            gpmat = bpy.data.materials.new(matName)
            bpy.data.materials.create_gpencil_data(gpmat)
            gpmat.grease_pencil.mode = 'BOX'
            gpmat.grease_pencil.stroke_style = 'TEXTURE'
            r,g,b = bpy.data.brushes['Pencil'].color            
            gpmat.grease_pencil.color = [r,g,b,0.99]

            gpmat.grease_pencil.mix_stroke_factor = self.penConfig['mixColor']
            gptexturepath= 'C:\\Users\\laish\\SurfaceStudio\\Assets\\Brush\\Penkuzhi02-top.png'
            gptexturepath= self.penConfig['penPath']
            image = bpy.data.images.load(gptexturepath)
            gpmat.grease_pencil.stroke_image = image
            gpencil.data.materials.append(gpmat)
        layer = gpencil_data.layers.new("GPPenLayer")
        frame = layer.frames.new(0)
        stroke = frame.strokes.new()
        stroke.line_width = 500    
        stroke.points.add(1)
        stroke.points[0].co = (0.0, 0.0, 0.0)
        stroke.points[0].pressure = 20
#        bpy.context.scene.tool_settings.gpencil_paint.color_mode = 'MATERIAL'
        return gpencil

    def penDrawing(self, GPName=None):        
        GPPen = self.createGP(GPName)

        GPWriteMat = GPPen.active_material
        for i, frame in enumerate(self.penConfig['penFrames']):
            
            x, y, z = self.penConfig['penLocation'][i]
            GPPenLocation = [x, y-1, z]
            GPPen.location = GPPenLocation
            GPPen.keyframe_insert(data_path="location", frame=frame)
            
            rotation_angle = math.sin(frame/100) / 10
            GPPen.rotation_mode = 'XYZ'
            GPPen.rotation_euler[1] = rotation_angle
            GPPen.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            if i<len(self.penConfig['penFrames'])-1:
                GPWriteMat.grease_pencil.color = self.penConfig['penColor'][i]
                GPWriteMat.grease_pencil.keyframe_insert(data_path='color', frame=frame)
            
    def penPlay(self):
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(0)
        bpy.ops.screen.animation_play()

    def centerView(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                view_3d = area.spaces[0].region_3d
                break
        view_3d.view_location = (0.0, 0.0, 0.0)
        
    def initWrite(self):
        for gp in bpy.data.grease_pencils:
            bpy.data.grease_pencils.remove(gp)
        for mat in bpy.data.materials:
            bpy.data.materials.remove(mat)
        for img in bpy.data.images:
            bpy.data.images.remove(img)
            
        for sound in bpy.data.sounds:
            bpy.data.sounds.remove(sound)

        sequencer = bpy.context.scene.sequence_editor
        if sequencer:
            for strip in sequencer.sequences_all:
                sequencer.sequences.remove(strip)
        bpy.context.scene.sequence_editor_clear()        


                  
        def createGPWrite(GPName='GPWrite'):        
            gpencil_data = bpy.data.grease_pencils.new(GPName)
            gpencil = bpy.data.objects.new(gpencil_data.name, gpencil_data)
            bpy.context.collection.objects.link(gpencil)
            
            gpencil_data["speed"] = 1.0
            
            matName = GPName + 'Mat'
            if matName in bpy.data.materials.keys():
                gpmat = bpy.data.materials[GPName]
            else:
                gpmat = bpy.data.materials.new(matName)
                bpy.data.materials.create_gpencil_data(gpmat)
                gpmat.grease_pencil.mode = 'DOTS'
                gpmat.grease_pencil.stroke_style = 'TEXTURE'
                bpy.data.materials[-1].grease_pencil.color = (1,1,1,1)
                bpy.data.materials[-1].grease_pencil.mix_stroke_factor = 0.9
                gptexturepath='C:\\Users\\laish\\SurfaceStudio\\Assets\\Brush\\maobi03.png'
                image = bpy.data.images.load(gptexturepath)
                gpmat.grease_pencil.stroke_image = image
                gpencil.data.materials.append(gpmat)
                
            layerName = GPName + 'Layer'    
            layer = gpencil_data.layers.new(layerName)    
        #    frame = layer.frames.new(1)
            
            bpy.context.view_layer.objects.active = gpencil
            gpencil.select_set(True)
            bpy.ops.gpencil.paintmode_toggle()
        #    bpy.data.brushes['Pencil'].color = (1,1,1)
                
            return gpencil



        refpos = (0, 0, 0)
        def createGPRef(GPName='GPRef'):        
            refgpencil_data = bpy.data.grease_pencils.new(GPName)
            refgpencil = bpy.data.objects.new(refgpencil_data.name, refgpencil_data)
            bpy.context.collection.objects.link(refgpencil)
            matName = GPName + 'Mat'
            if 'GPRefMat' in bpy.data.materials.keys():
                gpmat = bpy.data.materials[matName]
                gpencil.data.materials.appref(gpmat)
            else:
                refmat = bpy.data.materials.new(matName)
                bpy.data.materials.create_gpencil_data(refmat)
                refmat.grease_pencil.mode = 'BOX'
                refmat.grease_pencil.stroke_style = 'TEXTURE'
                bpy.data.materials[-1].grease_pencil.color = (1,1,1,1)
                bpy.data.materials[-1].grease_pencil.mix_stroke_factor = 0.0
                refpath='C:\\Users\\laish\\SurfaceStudio\\Assets\\Ref\\ref01.jpg'
                refimage = bpy.data.images.load(refpath)
                refmat.grease_pencil.stroke_image = refimage
                refgpencil.data.materials.append(refmat)
            layer = refgpencil_data.layers.new("GPRefLayer")  
            layer.hide = True  
            # 在图层中创建一个新的画笔
            frame = layer.frames.new(0)
            stroke = frame.strokes.new()
        #    stroke.stroke_cap_mode = 'SQUARE'
            stroke.line_width = 10    
            stroke.points.add(1)
            stroke.points[0].co = refpos
            stroke.points[0].pressure = 100            
            return refgpencil

        GPRef = createGPRef(GPName='GPRef')
        GPWrite = createGPWrite(GPName='GPWrite')

        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(0)



GPWrite = GPWriting('GPWrite')
audioFrames = GPWrite.audioFrames
audioVolume = GPWrite.deduplicationByFrames(attrName = 'pressure')    
strokeFrames = GPWrite.sortFrames()
strokePressure = GPWrite.getStrokeAttr('pressure')
strokeCo = GPWrite.getStrokeAttr('co')
strokeTime = GPWrite.getStrokeAttr('time')
fps = bpy.context.scene.render.fps
strokeSpaceFrames = GPWrite.strokeSpaceFrames

for i in range(len(strokeTime)):
    for j in range(len(strokeTime[i])):
        if strokeTime[i][j] == 0 and j < len(strokeTime[i])-1 and j > 0:          
            strokeFrames[i][j] = 0
            strokePressure[i][j] = 0


basePath = "C://Users//laish//SurfaceStudio//Work//Blender//Sound//chalk//"
file_list = os.listdir(basePath)
start_path = [basePath+file for file in file_list if file.startswith('start')]
middle_path = [basePath+file for file in file_list if file.startswith('middle')]
input_file = r"C:\Users\laish\SurfaceStudio\Work\Blender\Sound\chalk\test.wav"
output_file = r"C:\Users\laish\SurfaceStudio\Work\Blender\Sound\strokeSound\test-strokeVoice.wav"



sample_rate = 44100
sample_width = 2
num_channels = 2
compression_type = "NONE"

class AudioMix(GPWriting):
    def __init__(self, output_file):
#        super().__init__(state)
        self.output_file = output_file

        
    def linear_resample(self, original_list, new_length):
        if new_length <= 0:
            return []
        elif new_length == 1:
            return [original_list[0]]
        
        resampled_list = []
        step_size = (len(original_list) - 1) / (new_length - 1)
        
        for i in range(int(new_length)):
            index1 = int(i * step_size)
            index2 = min(index1 + 1, len(original_list) - 1)
            
            t = i * step_size - index1
            value = original_list[index1] * (1 - t) + original_list[index2] * t        
            resampled_list.append(value)
        
        return resampled_list

    def shiftList(self, lst, n):
        n = n % len(lst)
        return lst[n:] + lst[:n]


    def getCoLength(self):
        colens = []
        for i in range(len(strokeCo)):
            strokeLen = []
            for j in range(len(strokeCo[i])):
                if j < len(strokeCo[i]) - 1:
                    co1 = mathutils.Vector(strokeCo[i][j])
                    co2 = mathutils.Vector(strokeCo[i][j+1])
                    colen = (co2 - co1).length
                    strokeLen.append(colen)
            colens.append(strokeLen)
        return colens

    def getAudioInfo(self, audioPath):
        audioInfo = {}
        with wave.open(audioPath, "rb") as wav_file:
            # 获取WAV文件的相关信息
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            bit_depth = sample_width * 8
            num_frames = wav_file.getnframes()
            
            # 获取WAV文件的采样数据
            raw_data = wav_file.readframes(num_frames)

            # 将采样数据存储为列表
            samples = []  
            for i in range(0, len(raw_data), sample_width):
                sample = int.from_bytes(raw_data[i:i+sample_width], byteorder="little", signed=True)
                sample = max(min(sample, 32767), -32768)  # 限制取值范围在 -32768 到 32767 之间
                samples.append(sample)
                
            audioInfo = {
                "num_channels": num_channels,
                "sample_rate": sample_rate,
                "sample_width": sample_width,
                "bit_depth": bit_depth,
                "num_frames": num_frames,
                "samples": samples
            }
            
        return audioInfo

    def resampleAudio(self, volume = 1, startVolume = 0.8, middleVolume=0.2):
        sampleAudio = []        
        strokeFrameLen = len(strokeFrames)
        for idx in range(strokeFrameLen):
            startFrame = strokeFrames[idx][0]
            endFrame = strokeFrames[idx][-1]
            sampleTime = (endFrame-startFrame)/fps           
      
            spaceCycles = int(strokeSpaceFrames/fps * sample_rate * sample_width)
            
            if idx == strokeFrameLen - 1:
                spressureSpace = []
            else:
                spressureSpace = [0] * spaceCycles
      
            
            sampleNum = int(sampleTime * sample_rate * sample_width)        
            newstrokePressure = self.linear_resample(strokePressure[idx], sampleNum)
            newSamplePressure = newstrokePressure + spressureSpace

            
            startRandomPath= random.choice(start_path)    
            strokeStartAudio = self.getAudioInfo(startRandomPath)        
            middleRandomPath= random.choice(middle_path)    
            strokeMiddleAudio = self.getAudioInfo(middleRandomPath)
            realStartAudio = strokeStartAudio['samples']
            realMiddleAudio = strokeMiddleAudio['samples']
               
            realStartAudio = list(map(lambda x: x * startVolume, realStartAudio))
            realMiddleAudio = list(map(lambda x: x * middleVolume, realMiddleAudio))
            
            realStartAudioLen = len(realStartAudio)
            realMiddleAudioLen = len(realMiddleAudio)
            cycleTimes = math.ceil((sampleNum-realStartAudioLen)/realMiddleAudioLen)
            if realStartAudioLen>sampleNum:
                realStartAudio = realStartAudio[:sampleNum]
                realStartAudioLen = sampleNum
                cycleTimes = 0
                
            newRealMiddleAudio = realMiddleAudio * cycleTimes
            lastEnd = sampleNum-realStartAudioLen
            realMiddleAudio = newRealMiddleAudio[:lastEnd]
            audioSamples = realStartAudio + realMiddleAudio + spressureSpace
                    
            for i in range(len(audioSamples)):
                sampleAudio.append(audioSamples[i])

        return sampleAudio


    def saveWav(self, samples, wavPath):
        samples = [max(min(int(s), 32767), -32768) for s in samples]
        samples_bytes = b"".join([struct.pack("<h", int(s)) for s in samples])
        # 将音频数据写入 WAV 文件
        with wave.open(wavPath, "wb") as wav_file:
            wav_file.setframerate(sample_rate)
            wav_file.setsampwidth(sample_width)
            wav_file.setnchannels(num_channels)
            wav_file.setcomptype(compression_type, "notused")

            # 设置 WAV 文件的其他属性
            params = (
                num_channels,
                sample_width,
                sample_rate,
                len(samples),
                compression_type,""
            )
            wav_file.setparams(params)
            wav_file.writeframes(samples_bytes)

    def createSequences(self, wavPath):
        bpy.context.scene.sequence_editor_create()
        GPWritingSong = bpy.context.scene.sequence_editor.sequences.new_sound("GPWritingSong", wavPath, 1, 1)
        GPWritingSong.show_waveform = True
        # 获取声音的长度（以帧为单位）
        sound_length = GPWritingSong.frame_final_duration




audioMix = AudioMix(output_file)

samples = audioMix.resampleAudio(volume = 1, startVolume = 0.9, middleVolume=0.2)
audioMix.saveWav(samples, output_file)
audioMix.createSequences(output_file)