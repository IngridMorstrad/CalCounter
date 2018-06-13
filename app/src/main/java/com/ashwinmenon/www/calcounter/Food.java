package com.ashwinmenon.www.calcounter;

/**
 * Created by TheAshman on 1/26/2017.
 */

class Food {
    private int calories;
    private int proteins;
    private final String name;

    public Food(String foodName) {
        this(foodName, 0, 0);
    }

    public Food(String foodName, int foodCalories, int foodProteins) {
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

    public String getCalories() { return String.valueOf(calories); }
    public String getProteins() { return String.valueOf(proteins); }
    public int getCaloriesInt() { return calories; }
    public int getProteinsInt() { return proteins; }
    public String getName() { return name; }
    public void setCalories(int val) { calories = val; }
    public void setProteins(int val) { proteins = val; }

    @Override
    public String toString() {
        String DELIM = "<";
        return getName()+ DELIM + getCalories() + DELIM + getProteins();
    }
}
