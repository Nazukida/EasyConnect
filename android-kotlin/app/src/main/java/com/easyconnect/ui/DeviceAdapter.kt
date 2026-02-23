package com.easyconnect.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.easyconnect.databinding.ItemDeviceBinding
import com.easyconnect.model.Device

class DeviceAdapter(
    private val onDeviceClick: (Device) -> Unit
) : ListAdapter<Device, DeviceAdapter.DeviceViewHolder>(DeviceDiffCallback()) {
    
    private var selectedPosition = -1
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DeviceViewHolder {
        val binding = ItemDeviceBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return DeviceViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: DeviceViewHolder, position: Int) {
        val device = getItem(position)
        holder.bind(device, position == selectedPosition)
        
        holder.itemView.setOnClickListener {
            val previousPosition = selectedPosition
            selectedPosition = holder.adapterPosition
            
            if (previousPosition != -1) {
                notifyItemChanged(previousPosition)
            }
            notifyItemChanged(selectedPosition)
            
            onDeviceClick(device)
        }
    }
    
    fun getSelectedDevice(): Device? {
        return if (selectedPosition >= 0 && selectedPosition < itemCount) {
            getItem(selectedPosition)
        } else null
    }
    
    fun clearSelection() {
        val previous = selectedPosition
        selectedPosition = -1
        if (previous != -1) {
            notifyItemChanged(previous)
        }
    }
    
    class DeviceViewHolder(
        private val binding: ItemDeviceBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(device: Device, isSelected: Boolean) {
            binding.tvDeviceName.text = device.name
            binding.tvDeviceIp.text = device.ip
            
            // 选中状态
            binding.root.isChecked = isSelected
            binding.root.strokeWidth = if (isSelected) 4 else 0
        }
    }
    
    class DeviceDiffCallback : DiffUtil.ItemCallback<Device>() {
        override fun areItemsTheSame(oldItem: Device, newItem: Device): Boolean {
            return oldItem.ip == newItem.ip
        }
        
        override fun areContentsTheSame(oldItem: Device, newItem: Device): Boolean {
            return oldItem == newItem
        }
    }
}
