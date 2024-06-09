from ultralytics import YOLO
import torch
class build_yolo_people_detection():
    def __init__(self):
        """
        build yolo model trained by auair
        """
        self.model=YOLO(r'downstream_task/detection/best.pt')

    def predict(self,frame):
        '''
        frame: 1 frame only.
        有八类标签
        x[list] 只取第一个frame 到时候是frame list
        '''
        x=self.model.predict(frame,classes=[0,1,2,3,4,5,6,7])
        x=x[0]
        # print(x[0])
        cls,conf=torch.tensor([]),torch.tensor([])
        # conf=[]
        res = x.boxes.xywh
        if res.numel()>0:
            cls=x.cls.int()
            conf=x.conf
        return [res,cls,conf]
    
    def process_box(self,result):
        '''
        tensor[n,4]
        '''
        n ,_ = result.shape
        output=torch.zeros(n,4)
        # if result.numel() > 0:
            # print(result)
        output[:,1]=result[:, 1]-result[:,3]/2.0
        output[:,2]=result[:, 2]-result[:,4]/2.0
        output[:,3:]=result[:,3:]      
        return output.int()
    
if __name__=='__main__':
    model=build_yolo_people_detection()
    x=torch.zeros(1,3,512,512)
    res = model.predict(x)
    # print(res)
    # print(output.boxes)