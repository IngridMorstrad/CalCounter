package com.ashwinmenon.www.calcounter.db;

import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import java.util.List;

@Dao
public interface FoodDao {
    @Query("SELECT * FROM food")
    List<Food> getAll();

    @Query("SELECT * FROM food WHERE dayId LIKE :dayId")
    List<Food> loadAllByDayId(int dayId);

    @Query("SELECT * FROM food WHERE name LIKE :name LIMIT 1")
    Food findByName(String name);

    @Insert
    void insertAll(Food... foods);

    @Delete
    void delete(Food food);

    @Update(onConflict = OnConflictStrategy.REPLACE)
    void updateAll(Food... foods);
}
