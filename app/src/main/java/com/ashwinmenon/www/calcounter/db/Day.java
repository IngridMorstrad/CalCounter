package com.ashwinmenon.www.calcounter.db;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
public class Day {
    @PrimaryKey
    public final int dayId;
    private String date;

    public Day(int dayId, String date) {
        this.dayId = dayId;
        this.date = date;
    }

    @Override
    public String toString() {
        return date;
    }

}
