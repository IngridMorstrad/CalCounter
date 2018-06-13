package com.ashwinmenon.www.calcounter;

/**
 * Created by TheAshman on 1/26/2017.
 */

class Food {
    private Integer calories;
    private Integer proteins;
    private final String name;

    public Food(String foodName) {
        this(foodName, 0, 0);
    }

    public Food(String foodName, Integer foodCalories, Integer foodProteins) {
        name = foodName;
        calories = foodCalories;
        proteins = foodProteins;
    }

    public String getRatio() {
        String ratio;
        if (proteins == 0) {
            ratio = "Get some more protein!";
        }
        else {
            ratio = String.format("%.2f", (double)calories/proteins);
        }
        return ratio;
    }

    public String getCalories() { return calories.toString(); }
    public String getProteins() { return proteins.toString(); }
    public Integer getCaloriesInt() { return calories; }
    public Integer getProteinsInt() { return proteins; }
    public String getName() { return name; }
    public void setCalories(Integer val) { calories = val; }
    public void setProteins(Integer val) { proteins = val; }

    @Override
    public String toString() {
        String DELIM = "<";
        return getName()+ DELIM +getCalories()+ DELIM +getProteins();
    }
}
