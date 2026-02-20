// Cluster 29

package com.acmeair.web.dto;

import javax.xml.bind.annotation.XmlElement;



public class BookingPKInfo {

	@XmlElement(name="id")
	private String id;
	
	@XmlElement(name="customerId")
	private String customerId;
	
	public BookingPKInfo() {
		
	}


	public BookingPKInfo(String customerId,String id) {
		
		this.id = id;
		this.customerId = customerId;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getCustomerId() {
		return customerId;
	}

	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}
}


// Node: setCustomerId
package com.acmeair.web.dto;

import java.util.Date;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.Booking;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="Booking")
public class BookingInfo {

	@XmlElement(name="bookingId")
	private String bookingId;	
	
	@XmlElement(name="flightId")
	private String flightId;
	
	@XmlElement(name="customerId")
	private String customerId;
	
	@XmlElement(name="dateOfBooking")
	private Date dateOfBooking;
	
	@XmlElement(name="pkey")
	private BookingPKInfo pkey;
	
	public BookingInfo() {
		
	}

	public BookingInfo(Booking booking){
		this.bookingId = booking.getBookingId();
		this.flightId = booking.getFlightId();
		this.customerId = booking.getCustomerId();
		this.dateOfBooking = booking.getDateOfBooking();
		this.pkey = new BookingPKInfo(this.customerId, this.bookingId);
	}
	
	
	public String getBookingId() {
		return bookingId;
	}
	public void setBookingId(String bookingId) {
		this.bookingId = bookingId;
	}
	public String getFlightId() {
		return flightId;
	}
	public void setFlightId(String flightId) {
		this.flightId = flightId;
	}
	public String getCustomerId() {
		return customerId;
	}
	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}
	public Date getDateOfBooking() {
		return dateOfBooking;
	}
	public void setDateOfBooking(Date dateOfBooking) {
		this.dateOfBooking = dateOfBooking;
	}	
	public BookingPKInfo getPkey(){
		return pkey;
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

import com.acmeair.entities.BookingPK;

import com.ibm.websphere.objectgrid.plugins.PartitionableKey;

public class BookingPKImpl implements BookingPK, Serializable, PartitionableKey {
	
	private static final long serialVersionUID = 1L;
	private String id;
	private String customerId;
	
	public BookingPKImpl() {
		super();
	}

	public BookingPKImpl(String customerId,String id) {
		super();
		this.id = id;
		this.customerId = customerId;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getCustomerId() {
		return customerId;
	}

	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}

	@Override
	public Object ibmGetPartition() {
		return this.customerId;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result
				+ ((customerId == null) ? 0 : customerId.hashCode());
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
		BookingPKImpl other = (BookingPKImpl) obj;
		if (customerId == null) {
			if (other.customerId != null)
				return false;
		} else if (!customerId.equals(other.customerId))
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
		return "BookingPK [customerId=" + customerId + ",id=" + id + "]";
	}

	
}


