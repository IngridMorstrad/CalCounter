package com.ashwinmenon.www.calcounter;

import android.app.Activity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

import com.ashwinmenon.www.calcounter.db.Food;

import java.util.List;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * Created by TheAshman on 1/26/2017.
 */

class FoodAdapter extends ArrayAdapter<Food> {

    FoodAdapter(Activity context, List<Food> w) {
        super(context, 0, w);
    }

    @NonNull
    @Override
    public View getView(int position, @Nullable View convertView, @NonNull ViewGroup parent) {
        // Check if the existing view is being reused, otherwise inflate the view
        View listItemView = convertView;
        if(listItemView == null) {
            listItemView = LayoutInflater.from(getContext()).inflate(
                    R.layout.list_item, parent, false);
        }

        // Get the food object located at this position in the list
        Food currentFood = getItem(position);

        // Set the TextViews in the list item viewgroup
        TextView foodNameTextView = listItemView.findViewById(R.id.food_name_text_view);
        foodNameTextView.setText(currentFood.getName());

        TextView calsTextView = listItemView.findViewById(R.id.calories_text_view);
        calsTextView.setText(currentFood.getCaloriesAsStr());

        TextView proteinTextView = listItemView.findViewById(R.id.proteins_text_view);
        proteinTextView.setText(currentFood.getProteinsAsStr());

        TextView ratioTextView = listItemView.findViewById(R.id.ratio_text_view);
        ratioTextView.setText(currentFood.getRatio());

        // TODO: Add indicators indicating how good/bad the food was
        //listItemView.setBackgroundColor(ContextCompat.getColor(getContext(), R.color.));

        // Return the whole list item layout
        // so that it can be shown in the ListView
        return listItemView;
    }
}