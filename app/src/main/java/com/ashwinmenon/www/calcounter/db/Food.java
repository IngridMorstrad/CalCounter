package com.ashwinmenon.www.calcounter.db;

import androidx.room.ColumnInfo;
import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.PrimaryKey;

import lombok.Getter;
import lombok.Setter;

import static androidx.room.ForeignKey.CASCADE;

/**
 * Created by TheAshman on 1/26/2017.
 */

@Entity(foreignKeys = @ForeignKey(entity = Day.class,
        parentColumns = "dayId",
        childColumns = "dayId",
        onDelete = CASCADE))
@Getter
@Setter
public class Food {
    @PrimaryKey(autoGenerate = true)
    int food_id;
    @ColumnInfo(name = "name")
    String name;
    @ColumnInfo(name = "calories")
    int calories;
    @ColumnInfo(name = "proteins")
    int proteins;
    @ColumnInfo(name = "dayId")
    int dayId;

    public Food() {
        this.name = "default";
    }

    public Food(String name, int calories, int proteins, int day_id) {
        this.name = name;
        this.calories = calories;
        this.proteins = proteins;
        this.dayId = day_id;
    }

    public String getRatio() {
        String ratio;
        if (proteins == 0) {
            ratio = "Get some more protein!";
        } else {
            ratio = String.format("%.2f", (double)calories/proteins);
        }
        return ratio;
    }

    public String getCaloriesAsStr() { return String.valueOf(calories); }
    public String getProteinsAsStr() { return String.valueOf(proteins); }
}
