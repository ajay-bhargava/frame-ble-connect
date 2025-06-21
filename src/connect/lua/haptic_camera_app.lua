local data = require('data.min')
local camera = require('camera.min')

-- Phone to Frame flags
CAPTURE_SETTINGS_MSG = 0x0d
TOUCH_EVENT_MSG = 0x0e  -- New message type for touch events

-- register the message parser so it's automatically called when matching data comes in
data.parsers[CAPTURE_SETTINGS_MSG] = camera.parse_capture_settings

-- Touch detection variables
local last_touch_time = 0
local touch_threshold = 0.5  -- seconds between touches to prevent spam
local is_touch_enabled = true

-- IMU sensor variables for touch detection
local last_accel = {x = 0, y = 0, z = 0}
local accel_threshold = 2.0  -- acceleration change threshold for touch detection
local gyro_threshold = 1.0   -- gyroscope threshold for movement detection

function clear_display()
    frame.display.text(" ", 1, 1)
    frame.display.show()
    frame.sleep(0.04)
end

function show_flash()
    frame.display.bitmap(241, 191, 160, 2, 0, string.rep("\xFF", 400))
    frame.display.bitmap(311, 121, 20, 2, 0, string.rep("\xFF", 400))
    frame.display.show()
    frame.sleep(0.04)
end

function show_touch_indicator()
    -- Show a small indicator that touch was detected
    frame.display.text("T", 1, 1)
    frame.display.show()
    frame.sleep(0.1)
    clear_display()
end

function detect_touch()
    -- Get current IMU data
    local accel = frame.imu.accelerometer()
    local gyro = frame.imu.gyroscope()
    
    if not accel or not gyro then
        return false
    end
    
    -- Calculate acceleration change
    local accel_change = math.abs(accel.x - last_accel.x) + 
                        math.abs(accel.y - last_accel.y) + 
                        math.abs(accel.z - last_accel.z)
    
    -- Calculate gyroscope magnitude
    local gyro_magnitude = math.sqrt(gyro.x^2 + gyro.y^2 + gyro.z^2)
    
    -- Check if this looks like a touch event
    local current_time = frame.time()
    local time_since_last_touch = current_time - last_touch_time
    
    if accel_change > accel_threshold and 
       gyro_magnitude < gyro_threshold and 
       time_since_last_touch > touch_threshold then
        
        -- Update last touch time
        last_touch_time = current_time
        
        -- Update last accelerometer reading
        last_accel = {x = accel.x, y = accel.y, z = accel.z}
        
        return true
    end
    
    -- Update last accelerometer reading
    last_accel = {x = accel.x, y = accel.y, z = accel.z}
    
    return false
end

function trigger_photo_capture()
    if not is_touch_enabled then
        return
    end
    
    -- Show touch indicator
    show_touch_indicator()
    
    -- Create capture settings for 720p
    local capture_settings = {
        resolution = 720
    }
    
    -- Trigger photo capture
    local rc, err = pcall(camera.capture_and_send, capture_settings)
    
    if rc == false then
        print("Touch capture failed: " .. tostring(err))
    else
        print("Touch-triggered photo captured")
    end
end

-- Main app loop
function app_loop()
    clear_display()

    -- tell the host program that the frameside app is ready (waiting on await_print)
    print('Haptic camera app is running - touch to capture!')

    while true do
        rc, err = pcall(
            function()
                -- process any raw data items, if ready (parse into take_photo, then clear data.app_data_block)
                local items_ready = data.process_raw_items()

                if items_ready > 0 then
                    if (data.app_data[CAPTURE_SETTINGS_MSG] ~= nil) then
                        -- visual indicator of capture and send
                        show_flash()
                        rc, err = pcall(camera.capture_and_send, data.app_data[CAPTURE_SETTINGS_MSG])
                        clear_display()

                        if rc == false then
                            print(err)
                        end

                        data.app_data[CAPTURE_SETTINGS_MSG] = nil
                    end
                end

                -- Check for touch events
                if detect_touch() then
                    trigger_photo_capture()
                end

                if camera.is_auto_exp then
                    camera.run_auto_exposure()
                end

                frame.sleep(0.05)  -- Faster polling for touch detection
            end
        )
        -- Catch the break signal here and clean up the display
        if rc == false then
            -- send the error back on the stdout stream
            print(err)
            frame.display.text(" ", 1, 1)
            frame.display.show()
            frame.sleep(0.04)
            break
        end
    end
end

-- run the main app loop
app_loop() 