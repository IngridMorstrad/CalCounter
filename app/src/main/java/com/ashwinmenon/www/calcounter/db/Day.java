package com.ashwinmenon.www.calcounter.db;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity
public class Day {
    @PrimaryKey
    public int dayId;
    public String date;

    public Day(int dayId, String date) {
        this.dayId = dayId;
        this.date = date;
    }

    public int getDayId() { return dayId; }
    public void setDayId(int dayId) { this.dayId = dayId; }
    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }

    @Override
    public String toString() {
        return date;
    }
}
