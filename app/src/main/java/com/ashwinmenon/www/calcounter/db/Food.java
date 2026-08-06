package com.ashwinmenon.www.calcounter.db;

import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.PrimaryKey;

import static androidx.room.ForeignKey.CASCADE;

@Entity(foreignKeys = @ForeignKey(entity = Day.class,
        parentColumns = "dayId",
        childColumns = "dayId",
        onDelete = CASCADE))
public class Food {
    @PrimaryKey(autoGenerate = true)
    public int food_id;
    @ColumnInfo(name = "name")
    public String name;
    @ColumnInfo(name = "calories")
    public int calories;
    @ColumnInfo(name = "proteins")
    public int proteins;
    @ColumnInfo(name = "dayId")
    public int dayId;

    public Food() {
        this.name = "default";
    }

    public Food(String name, int calories, int proteins, int dayId) {
        this.name = name;
        this.calories = calories;
        this.proteins = proteins;
        this.dayId = dayId;
    }

    public int getFood_id() { return food_id; }
    public void setFood_id(int food_id) { this.food_id = food_id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getCalories() { return calories; }
    public void setCalories(int calories) { this.calories = calories; }
    public int getProteins() { return proteins; }
    public void setProteins(int proteins) { this.proteins = proteins; }
    public int getDayId() { return dayId; }
    public void setDayId(int dayId) { this.dayId = dayId; }

    public String getRatio() {
        if (proteins == 0) {
            return "Get some more protein!";
        }
        return String.format("%.2f", (double) calories / proteins);
    }

    public String getCaloriesAsStr() { return String.valueOf(calories); }
    public String getProteinsAsStr() { return String.valueOf(proteins); }
}
