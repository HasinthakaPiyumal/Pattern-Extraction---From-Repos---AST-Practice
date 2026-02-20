// Cluster 17

package com.acmeair.web.dto;

import java.math.BigDecimal;
import java.util.Date;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.Flight;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="Flight")
public class FlightInfo {
	
	@XmlElement(name="_id")
	private String _id;	
	private String flightSegmentId;		
	private Date scheduledDepartureTime;
	private Date scheduledArrivalTime;
	private BigDecimal firstClassBaseCost;
	private BigDecimal economyClassBaseCost;
	private int numFirstClassSeats;
	private int numEconomyClassSeats;
	private String airplaneTypeId;
	private FlightSegmentInfo flightSegment;
	
	@XmlElement(name="pkey")
	private FlightPKInfo pkey;
	
	public FlightInfo(){
		
	}
	
	public FlightInfo(Flight flight){
		this._id = flight.getFlightId();
		this.flightSegmentId = flight.getFlightSegmentId();
		this.scheduledDepartureTime = flight.getScheduledDepartureTime();
		this.scheduledArrivalTime = flight.getScheduledArrivalTime();
		this.firstClassBaseCost = flight.getFirstClassBaseCost();
		this.economyClassBaseCost = flight.getEconomyClassBaseCost();
		this.numFirstClassSeats = flight.getNumFirstClassSeats();
		this.numEconomyClassSeats = flight.getNumEconomyClassSeats();
		this.airplaneTypeId = flight.getAirplaneTypeId();
		if(flight.getFlightSegment() != null){
			this.flightSegment = new FlightSegmentInfo(flight.getFlightSegment());
		} else {
			this.flightSegment = null;
		}
		this.pkey = new FlightPKInfo(this.flightSegmentId, this._id);
	}
	
	public String get_id() {
		return _id;
	}
	public void set_id(String _id) {
		this._id = _id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
	public Date getScheduledDepartureTime() {
		return scheduledDepartureTime;
	}
	public void setScheduledDepartureTime(Date scheduledDepartureTime) {
		this.scheduledDepartureTime = scheduledDepartureTime;
	}
	public Date getScheduledArrivalTime() {
		return scheduledArrivalTime;
	}
	public void setScheduledArrivalTime(Date scheduledArrivalTime) {
		this.scheduledArrivalTime = scheduledArrivalTime;
	}
	public BigDecimal getFirstClassBaseCost() {
		return firstClassBaseCost;
	}
	public void setFirstClassBaseCost(BigDecimal firstClassBaseCost) {
		this.firstClassBaseCost = firstClassBaseCost;
	}
	public BigDecimal getEconomyClassBaseCost() {
		return economyClassBaseCost;
	}
	public void setEconomyClassBaseCost(BigDecimal economyClassBaseCost) {
		this.economyClassBaseCost = economyClassBaseCost;
	}
	public int getNumFirstClassSeats() {
		return numFirstClassSeats;
	}
	public void setNumFirstClassSeats(int numFirstClassSeats) {
		this.numFirstClassSeats = numFirstClassSeats;
	}
	public int getNumEconomyClassSeats() {
		return numEconomyClassSeats;
	}
	public void setNumEconomyClassSeats(int numEconomyClassSeats) {
		this.numEconomyClassSeats = numEconomyClassSeats;
	}
	public String getAirplaneTypeId() {
		return airplaneTypeId;
	}
	public void setAirplaneTypeId(String airplaneTypeId) {
		this.airplaneTypeId = airplaneTypeId;
	}
	public FlightSegmentInfo getFlightSegment() {
		return flightSegment;
	}
	public void setFlightSegment(FlightSegmentInfo flightSegment) {
		this.flightSegment = flightSegment;
	}
	public FlightPKInfo getPkey(){
		return pkey;
	}
}


// Node: setFlightSegmentId
package com.acmeair.web.dto;

public class FlightPKInfo {

	private String id;
	private String flightSegmentId;
	
	FlightPKInfo(){}
	FlightPKInfo(String flightSegmentId,String id){
		this.id = id;
		this.flightSegmentId = flightSegmentId;
	}
	
	public String getId() {
		return id;
	}
	public void setId(String id) {
		this.id = id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
}


/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.morphia.entities;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

import org.mongodb.morphia.annotations.Entity;
import org.mongodb.morphia.annotations.Id;

import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;

@Entity(value="flight")
public class FlightImpl implements Flight, Serializable{

	private static final long serialVersionUID = 1L;
	
	@Id
	private String _id;
	
	private String flightSegmentId;
		
	private Date scheduledDepartureTime;
	private Date scheduledArrivalTime;
	private BigDecimal firstClassBaseCost;
	private BigDecimal economyClassBaseCost;
	private int numFirstClassSeats;
	private int numEconomyClassSeats;
	private String airplaneTypeId;
	
	private FlightSegment flightSegment;
	
	public FlightImpl() {
	}
	
	public FlightImpl(String id, String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId) {
		this._id = id;
		this.flightSegmentId = flightSegmentId;
		this.scheduledDepartureTime = scheduledDepartureTime;
		this.scheduledArrivalTime = scheduledArrivalTime;
		this.firstClassBaseCost = firstClassBaseCost;
		this.economyClassBaseCost = economyClassBaseCost;
		this.numFirstClassSeats = numFirstClassSeats;
		this.numEconomyClassSeats = numEconomyClassSeats;
		this.airplaneTypeId = airplaneTypeId;
	}

	public String getFlightId(){
		return _id;
	}
	
	public void setFlightId(String id){
		this._id = id;
	}
	
	public String getFlightSegmentId()
	{
		return flightSegmentId;
	}
	
	public void setFlightSegmentId(String segmentId){
		this.flightSegmentId = segmentId;
	}
	
	public Date getScheduledDepartureTime() {
		return scheduledDepartureTime;
	}


	public void setScheduledDepartureTime(Date scheduledDepartureTime) {
		this.scheduledDepartureTime = scheduledDepartureTime;
	}


	public Date getScheduledArrivalTime() {
		return scheduledArrivalTime;
	}


	public void setScheduledArrivalTime(Date scheduledArrivalTime) {
		this.scheduledArrivalTime = scheduledArrivalTime;
	}


	public BigDecimal getFirstClassBaseCost() {
		return firstClassBaseCost;
	}


	public void setFirstClassBaseCost(BigDecimal firstClassBaseCost) {
		this.firstClassBaseCost = firstClassBaseCost;
	}


	public BigDecimal getEconomyClassBaseCost() {
		return economyClassBaseCost;
	}


	public void setEconomyClassBaseCost(BigDecimal economyClassBaseCost) {
		this.economyClassBaseCost = economyClassBaseCost;
	}


	public int getNumFirstClassSeats() {
		return numFirstClassSeats;
	}


	public void setNumFirstClassSeats(int numFirstClassSeats) {
		this.numFirstClassSeats = numFirstClassSeats;
	}


	public int getNumEconomyClassSeats() {
		return numEconomyClassSeats;
	}


	public void setNumEconomyClassSeats(int numEconomyClassSeats) {
		this.numEconomyClassSeats = numEconomyClassSeats;
	}


	public String getAirplaneTypeId() {
		return airplaneTypeId;
	}


	public void setAirplaneTypeId(String airplaneTypeId) {
		this.airplaneTypeId = airplaneTypeId;
	}


	public FlightSegment getFlightSegment() {
		return flightSegment;
	}

	public void setFlightSegment(FlightSegment flightSegment) {
		this.flightSegment = flightSegment;
	}

	@Override
	public String toString() {
		return "Flight key="+_id
				+ ", scheduledDepartureTime=" + scheduledDepartureTime
				+ ", scheduledArrivalTime=" + scheduledArrivalTime
				+ ", firstClassBaseCost=" + firstClassBaseCost
				+ ", economyClassBaseCost=" + economyClassBaseCost
				+ ", numFirstClassSeats=" + numFirstClassSeats
				+ ", numEconomyClassSeats=" + numEconomyClassSeats
				+ ", airplaneTypeId=" + airplaneTypeId + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		FlightImpl other = (FlightImpl) obj;
		if (airplaneTypeId == null) {
			if (other.airplaneTypeId != null)
				return false;
		} else if (!airplaneTypeId.equals(other.airplaneTypeId))
			return false;
		if (economyClassBaseCost == null) {
			if (other.economyClassBaseCost != null)
				return false;
		} else if (!economyClassBaseCost.equals(other.economyClassBaseCost))
			return false;
		if (firstClassBaseCost == null) {
			if (other.firstClassBaseCost != null)
				return false;
		} else if (!firstClassBaseCost.equals(other.firstClassBaseCost))
			return false;
		if (flightSegment == null) {
			if (other.flightSegment != null)
				return false;
		} else if (!flightSegment.equals(other.flightSegment))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (numEconomyClassSeats != other.numEconomyClassSeats)
			return false;
		if (numFirstClassSeats != other.numFirstClassSeats)
			return false;
		if (scheduledArrivalTime == null) {
			if (other.scheduledArrivalTime != null)
				return false;
		} else if (!scheduledArrivalTime.equals(other.scheduledArrivalTime))
			return false;
		if (scheduledDepartureTime == null) {
			if (other.scheduledDepartureTime != null)
				return false;
		} else if (!scheduledDepartureTime.equals(other.scheduledDepartureTime))
			return false;
		return true;
	}
	
	
}

/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.wxs.entities;

import java.io.Serializable;
import com.acmeair.entities.FlightPK;
import com.ibm.websphere.objectgrid.plugins.PartitionableKey;


public class FlightPKImpl implements FlightPK, Serializable, PartitionableKey {
	
	private static final long serialVersionUID = 1L;
	
	private String id;
	private String flightSegmentId;
	
	public FlightPKImpl() {
		super();
	}

	public FlightPKImpl(String flightSegmentId,String id) {
		super();
		this.id = id;
		this.flightSegmentId = flightSegmentId;
	}
	
	public String getId() {
		return id;
	}
	public void setId(String id) {
		this.id = id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
	
	@Override
	public Object ibmGetPartition() {
		return this.flightSegmentId;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result
				+ ((flightSegmentId == null) ? 0 : flightSegmentId.hashCode());
		result = prime * result + ((id == null) ? 0 : id.hashCode());
		return result;
	}
	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		FlightPKImpl other = (FlightPKImpl) obj;
		if (flightSegmentId == null) {
			if (other.flightSegmentId != null)
				return false;
		} else if (!flightSegmentId.equals(other.flightSegmentId))
			return false;
		if (id == null) {
			if (other.id != null)
				return false;
		} else if (!id.equals(other.id))
			return false;
		return true;
	}
	@Override
	public String toString() {
		return "FlightPK [flightSegmentId=" + flightSegmentId +",id=" + id+ "]";
	}
	
}


/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.wxs.entities;


import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;


public class FlightImpl implements Flight, Serializable{

	private static final long serialVersionUID = 1L;
				
	private FlightPKImpl pkey;
	private Date scheduledDepartureTime;
	private Date scheduledArrivalTime;
	private BigDecimal firstClassBaseCost;
	private BigDecimal economyClassBaseCost;
	private int numFirstClassSeats;
	private int numEconomyClassSeats;
	private String airplaneTypeId;
	
	private FlightSegment flightSegment;
	
	public FlightImpl() {
	}
	
	public FlightImpl(String id, String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId) {
		this.pkey = new FlightPKImpl(flightSegmentId,id);
		
		this.scheduledDepartureTime = scheduledDepartureTime;
		this.scheduledArrivalTime = scheduledArrivalTime;
		this.firstClassBaseCost = firstClassBaseCost;
		this.economyClassBaseCost = economyClassBaseCost;
		this.numFirstClassSeats = numFirstClassSeats;
		this.numEconomyClassSeats = numEconomyClassSeats;
		this.airplaneTypeId = airplaneTypeId;
	}

	public FlightPKImpl getPkey() {
		return pkey;
	}

	public void setPkey(FlightPKImpl pkey) {
		this.pkey = pkey;		
	}
	

	@Override
	public String getFlightId() {
		return pkey.getId();
	}

	@Override
	public void setFlightId(String id) {
		pkey.setId(id);		
	}

	
	// The method is needed for index calculation
	public String getFlightSegmentId()
	{
		return pkey.getFlightSegmentId();
	}
	
	public Date getScheduledDepartureTime() {
		return scheduledDepartureTime;
	}


	public void setScheduledDepartureTime(Date scheduledDepartureTime) {
		this.scheduledDepartureTime = scheduledDepartureTime;
	}


	public Date getScheduledArrivalTime() {
		return scheduledArrivalTime;
	}


	public void setScheduledArrivalTime(Date scheduledArrivalTime) {
		this.scheduledArrivalTime = scheduledArrivalTime;
	}


	public BigDecimal getFirstClassBaseCost() {
		return firstClassBaseCost;
	}


	public void setFirstClassBaseCost(BigDecimal firstClassBaseCost) {
		this.firstClassBaseCost = firstClassBaseCost;
	}


	public BigDecimal getEconomyClassBaseCost() {
		return economyClassBaseCost;
	}


	public void setEconomyClassBaseCost(BigDecimal economyClassBaseCost) {
		this.economyClassBaseCost = economyClassBaseCost;
	}


	public int getNumFirstClassSeats() {
		return numFirstClassSeats;
	}


	public void setNumFirstClassSeats(int numFirstClassSeats) {
		this.numFirstClassSeats = numFirstClassSeats;
	}


	public int getNumEconomyClassSeats() {
		return numEconomyClassSeats;
	}


	public void setNumEconomyClassSeats(int numEconomyClassSeats) {
		this.numEconomyClassSeats = numEconomyClassSeats;
	}


	public String getAirplaneTypeId() {
		return airplaneTypeId;
	}


	public void setAirplaneTypeId(String airplaneTypeId) {
		this.airplaneTypeId = airplaneTypeId;
	}


	public FlightSegment getFlightSegment() {
		return flightSegment;
	}

	public void setFlightSegment(FlightSegment flightSegment) {
		this.flightSegment = flightSegment;
	}

	@Override
	public String toString() {
		return "Flight key="+pkey
				+ ", scheduledDepartureTime=" + scheduledDepartureTime
				+ ", scheduledArrivalTime=" + scheduledArrivalTime
				+ ", firstClassBaseCost=" + firstClassBaseCost
				+ ", economyClassBaseCost=" + economyClassBaseCost
				+ ", numFirstClassSeats=" + numFirstClassSeats
				+ ", numEconomyClassSeats=" + numEconomyClassSeats
				+ ", airplaneTypeId=" + airplaneTypeId + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		FlightImpl other = (FlightImpl) obj;
		if (airplaneTypeId == null) {
			if (other.airplaneTypeId != null)
				return false;
		} else if (!airplaneTypeId.equals(other.airplaneTypeId))
			return false;
		if (economyClassBaseCost == null) {
			if (other.economyClassBaseCost != null)
				return false;
		} else if (!economyClassBaseCost.equals(other.economyClassBaseCost))
			return false;
		if (firstClassBaseCost == null) {
			if (other.firstClassBaseCost != null)
				return false;
		} else if (!firstClassBaseCost.equals(other.firstClassBaseCost))
			return false;
		if (flightSegment == null) {
			if (other.flightSegment != null)
				return false;
		} else if (!flightSegment.equals(other.flightSegment))
			return false;
		if (pkey == null) {
			if (other.pkey != null)
				return false;
		} else if (!pkey.equals(other.pkey))
			return false;
		if (numEconomyClassSeats != other.numEconomyClassSeats)
			return false;
		if (numFirstClassSeats != other.numFirstClassSeats)
			return false;
		if (scheduledArrivalTime == null) {
			if (other.scheduledArrivalTime != null)
				return false;
		} else if (!scheduledArrivalTime.equals(other.scheduledArrivalTime))
			return false;
		if (scheduledDepartureTime == null) {
			if (other.scheduledDepartureTime != null)
				return false;
		} else if (!scheduledDepartureTime.equals(other.scheduledDepartureTime))
			return false;
		return true;
	}


	/*
	public void setFlightSegmentId(String segmentId) {
		pkey.setFlightSegmentId(segmentId);
	}
	*/
	
}

