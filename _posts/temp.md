```java



class CarSeat{
    public long CarSeatId;
}

class CarSeatInfo{
    public CarSeat Seat;
    public boolean Avaliable;
    public long carId;
    public long beginTime;
}


boolean CanEntry(long carId){
    foreach(CarSeatInfo carSeatInfo in getAllCarSeatInfo){
        if(carSeatInfo.Avaliable){
            //考虑预锁，预占用
            return true;
        }
    }
    return false;
}

long Entry(long carId){
    if(CanEntry(carId)){
         foreach(CarSeatInfo carSeatInfo in getAllCarSeatInfo()){
        if(carSeatInfo.Avaliable){
            // 按车Id存储API
            carSeatInfo.Avliable = false;
            carSeatInfo.carId = carId;
            carSeatInfo.beginTime = now();
            return carSeatInfo.Seat.Id;
        }
    }else {
        throw new exception ;
    }
}

long Leave(long carId){
    //按车Id存储MAP
    //stream.api 
  foreach(CarSeatInfo carSeatInfo in getAllCarSeatInfo()){
    if(carSeatInfo.carId == carId){
        //计时信息

        long time= now() - carSeatInfo.beginTime ;
        carSeatInfo .avliable = false;
        //todo 计费信息
        return time;
    }
  }
  // throw new Exception .
  return -1;
}
//屋主，设计师，供应商，材料商
//
```