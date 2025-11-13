# Cluster 1

def voc_ap(rec, prec):
    """
    --- Official matlab code VOC2012---
    mrec=[0 ; rec ; 1];
    mpre=[0 ; prec ; 0];
    for i=numel(mpre)-1:-1:1
            mpre(i)=max(mpre(i),mpre(i+1));
    end
    i=find(mrec(2:end)~=mrec(1:end-1))+1;
    ap=sum((mrec(i)-mrec(i-1)).*mpre(i));
    """
    rec.insert(0, 0.0)
    rec.append(1.0)
    mrec = rec[:]
    prec.insert(0, 0.0)
    prec.append(0.0)
    mpre = prec[:]
    '\n     This part makes the precision monotonically decreasing\n        (goes from the end to the beginning)\n        matlab: for i=numel(mpre)-1:-1:1\n                    mpre(i)=max(mpre(i),mpre(i+1));\n    '
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    '\n     This part creates a list of indexes where the recall changes\n        matlab: i=find(mrec(2:end)~=mrec(1:end-1))+1;\n    '
    i_list = []
    for i in range(1, len(mrec)):
        if mrec[i] != mrec[i - 1]:
            i_list.append(i)
    '\n     The Average Precision (AP) is the area under the curve\n        (numerical integration)\n        matlab: ap=sum((mrec(i)-mrec(i-1)).*mpre(i));\n    '
    ap = 0.0
    for i in i_list:
        ap += (mrec[i] - mrec[i - 1]) * mpre[i]
    return (ap, mrec, mpre)

