package com.ashwinmenon.www.calcounter.db;

import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.List;

@Dao
public interface DayDao {
    @Query("SELECT * FROM day")
    List<Day> getAll();

    @Query("SELECT * from day LIMIT 1")
    Day[] getAnyDay();

    @Query("SELECT * FROM day WHERE dayId IN (:dayIds)")
    List<Day> loadAllByIds(int[] dayIds);

    @Insert
    void insert(Day day);

    @Insert
    void insertAll(Day... days);

    @Delete
    void delete(Day day);

    @Update
    void updateAll(Day... days);
}
