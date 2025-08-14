#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <math.h>

#include "freertos/FreeRTOS.h" //! RTOS FOR THE WIIIN
#include "freertos/task.h" //! Task included
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/twai.h"
#include "driver/uart.h"

#include "esp_log.h"
#include "esp_system.h"
#include <esp_timer.h>

#define TX_GPIO_NUM                     GPIO_NUM_21
#define RX_GPIO_NUM                     GPIO_NUM_22
#define TAG                     		"TWAI Controller"

#define ID_ESP32                        0x001
#define SDO_ID_DRIVER_1                 0x603
#define SDO_ID_DRIVER_2                 0x602
#define NMT_START_STOP_ID               0x0

#define R_PDO1_ID_DRIVER_1              0x203
#define R_PDO1_ID_DRIVER_2              0x202

#define R_PDO2_ID_DRIVER_1              0x303
#define R_PDO2_ID_DRIVER_2              0x302

#define TORQUE_MODE_ID 4
uint8_t start_op_mode_torque[8] = {0x2F,0x60,0x60,0x00,TORQUE_MODE_ID,0x00,0x00,0x00};

uint8_t positive_end[8] = {0x2B,0x06,0x30,0x10,0x02,0x00,0x00,0x00};
uint8_t negative_end[8] = {0x2B,0x06,0x30,0x0F,0x02,0x00,0x00,0x00};
uint8_t activate_rpdo2_d1[8] = {0x23,0x01,0x14,0x01,0x03,0x03,0x00,0x04};
uint8_t activate_rpdo2_d2[8] = {0x23,0x01,0x14,0x01,0x02,0x03,0x00,0x04};
uint8_t set_accel[8] = {0x23,0x83,0x60,0x00,0xD0,0x07,0x00,0x00};
uint8_t set_decel[8] = {0x23,0x84,0x60,0x00,0xA0,0x0F,0x00,0x00};
uint8_t target_vel[8] = {0x23, 0x81, 0x60, 0x00, 0xA0, 0x0F, 0x00, 0x00};
uint8_t nmt_start[2] = {0x01,0x00};
uint8_t rpdo2_1[6] = {0x00,0x00,0x00,0x00,0x00,0x00};
uint8_t rpdo2_2[6] = {0x06,0x00,0x00,0x00,0x00,0x00};
uint8_t rpdo2_3[6] = {0x0F,0x00,0x00,0x00,0x00,0x00};

uint8_t start_op_mode_pos[8] = {0x2F,0x60,0x60,0x00,0x01,0x00,0x00,0x00};

uint8_t velocity_search_limit[8] = {0x23,0x99,0x60,0x01,0xBC,0x02,0x00,0x00};
uint8_t velocity_move_away[8] = {0x23,0x99,0x60,0x02,0x64,0x00,0x00,0x00};
uint8_t rpdo1_1[2] = {0x00,0x00};
uint8_t rpdo1_2[2] = {0x06,0x00};
uint8_t rpdo1_3[2] = {0x0F,0x00};
uint8_t start_op_mode_home[8] = {0x2F,0x60,0x60,0x00,0x06,0x00,0x00,0x00};
uint8_t select_method_home[8] = {0x2F,0x98,0x60,0x00,0x11,0x00,0x00,0x00};
uint8_t start_home[2] = {0x1F,0x00};
uint8_t scale_pos_den[8] = {0x43,0x06,0x30,0x07,0x10,0x0E,0x00,0x00};
uint8_t scale_pos_den_read[8] = {0x40,0x06,0x30,0x07,0x00,0x00,0x00,0x00};

union IntToBytes {
    int num;
    unsigned char bytes[4];
};


uint8_t nmt_start_d1[2] = {0x01, 0x03}; // Start node 3
uint8_t nmt_start_d2[2] = {0x01, 0x02}; // Start node 2

twai_message_t heartbeat_msg = {
    .identifier = 0x702,  // 0x700 + node ID (Node 2 => 0x702)
    .data_length_code = 1,
    .data = {0x05},       // 0x05 = "Operational"
    .extd = 0, .rtr = 0
};


// CONFIG_USB_CONSOLE = 115200;
// Definiciones de pines

#define GPIO_DIR_CONTROL GPIO_NUM_25   // Pin para salida digital 1 o 0
#define PWM_OUTPUT_PIN GPIO_NUM_27    // Pin para salida PWM
#define GPIO_DIR_CONTROL2 GPIO_NUM_33   // Pin para salida digital 1 o 0
#define PWM_OUTPUT_PIN2 GPIO_NUM_26    // Pin para salida PWM
#define SENSOR GPIO_NUM_14    // Pin para sensor de proximidad
#define SENSOR_IR_B1 GPIO_NUM_19
#define SENSOR_IR_B2 GPIO_NUM_18

// Definiciones de PWM
#define PWM_FREQUENCY 5000   // Frecuencia de 5 kHz
#define PWM_FREQUENCY2 1000   // Frecuencia de 1 kHz
#define PWM_DUTY_CYCLE 50    // Ciclo de trabajo al 50%

static const twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(TX_GPIO_NUM, RX_GPIO_NUM, TWAI_MODE_NORMAL);
static const twai_timing_config_t t_config = TWAI_TIMING_CONFIG_50KBITS();
static const twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

float torque1 = 0.;
float torque2 = 0.;

int32_t prev_pose1 = 0.;
int32_t prev_pose2 = 0.;

int32_t pos1 = 0.;
int32_t pos2 = 0.;

int32_t curr_pos2 = 0.;
int32_t curr_pos1 = 0.;

int32_t delta1 = 0.;
int32_t delta2 = 0.;

static twai_message_t sdo_message = {
    // Message type and format settings
    .extd = 0,                // Standard Format message (11-bit ID)
    .rtr = 0,                 // Send a data frame
    .ss = 0,                  // Not single shot
    .self = 0,                // Not a self reception request
    .dlc_non_comp = 0,        // DLC is less than 8
    // Message ID and payload
    .identifier = SDO_ID_DRIVER_1,   // COB-ID, funcion + id del nodo al que va dirigido el mensaje
    .data_length_code = 8,
    .data = {1, 2, 3, 4, 5, 6, 7, 8},
};

static twai_message_t r_pdo2_message = {
    // Message type and format settings
    .extd = 0,                // Standard Format message (11-bit ID)
    .rtr = 0,                 // Send a data frame
    .ss = 0,                  // Not single shot
    .self = 0,                // Not a self reception request
    .dlc_non_comp = 0,        // DLC is less than 8
    // Message ID and payload
    .identifier = R_PDO2_ID_DRIVER_1,   // COB-ID, funcion + id del nodo al que va dirigido el mensaje
    .data_length_code = 6,
    .data = {1, 2, 3, 4, 5, 6},
};

static twai_message_t r_pdo1_message = {
    // Message type and format settings
    .extd = 0,                // Standard Format message (11-bit ID)
    .rtr = 0,                 // Send a data frame
    .ss = 0,                  // Not single shot
    .self = 0,                // Not a self reception request
    .dlc_non_comp = 0,        // DLC is less than 8
    // Message ID and payload
    .identifier = R_PDO1_ID_DRIVER_1,   // COB-ID, funcion + id del nodo al que va dirigido el mensaje
    .data_length_code = 2,
    .data = {1, 2},
};

static twai_message_t nmt_ss_message = {
    // Message type and format settings
    .extd = 0,                // Standard Format message (11-bit ID)
    .rtr = 0,                 // Send a data frame
    .ss = 0,                  // Not single shot
    .self = 0,                // Not a self reception request
    .dlc_non_comp = 0,        // DLC is less than 8
    // Message ID and payload
    .identifier = NMT_START_STOP_ID,   // COB-ID, funcion + id del nodo al que va dirigido el mensaje
    .data_length_code = 2,
    .data = {1, 2},
};

void send_can_message(twai_message_t type_message, int identifier, uint8_t* message, bool receive)
{
    type_message.identifier = identifier;
    for (int i = 0; i < type_message.data_length_code; i++) {
        type_message.data[i] = message[i];
    }
    twai_transmit(&type_message, portMAX_DELAY);
    if (receive){
		twai_message_t rx_msg;
		twai_receive(&rx_msg, portMAX_DELAY);
		uint64_t data = 0;
		if (rx_msg.identifier != ID_ESP32){
			for (int i = 0; i < rx_msg.data_length_code; i++) {
				data |= ((uint64_t)rx_msg.data[i] << (i * 8));
			}
		}
    }
}

void set_motor_torque(int driver, float torque_percent) {
    // Convert percentage to value (100.0% = 1000)
    int torque_value = (int)(torque_percent * 10.0f);
    
    // Ensure within safe limits (-3000 to +3000)
    if(torque_value < -3000) torque_value = -3000;
    if(torque_value > 3000) torque_value = 3000;
    
    // Prepare torque bytes (little-endian)
    uint8_t torque_bytes[2] = {
        torque_value & 0xFF,
        (torque_value >> 8) & 0xFF
    };
    
    // Build SDO message
    uint8_t set_torque[8] = {
        0x2B,           // Write 2-byte command
        0x71, 0x60,     // Object 6071h (Target Torque)
        0x00,           // Subindex 0
        torque_bytes[0], // Low byte
        torque_bytes[1], // High byte
        0x00,           // Padding
        0x00            // Padding
    };
    
    // Send to appropriate driver
    if (driver == 1) {
        send_can_message(sdo_message, SDO_ID_DRIVER_1, set_torque, 1);
    } else if (driver == 2) {
        send_can_message(sdo_message, SDO_ID_DRIVER_2, set_torque, 1);
    }
}

void init_torque_mode(int driver) {

    
    if (driver == 1) {
        // Set torque mode for driver 1
        send_can_message(sdo_message, SDO_ID_DRIVER_1, start_op_mode_torque, 1);
        vTaskDelay(pdMS_TO_TICKS(100));
        send_can_message(nmt_ss_message, NMT_START_STOP_ID, nmt_start, 0);
        // Enable drive
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_1, rpdo1_1, 0);
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_1, rpdo1_2, 0);
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_1, rpdo1_3, 1);
    }
    else if (driver == 2) {

        // Set torque mode for driver 2
        send_can_message(sdo_message, SDO_ID_DRIVER_2, start_op_mode_torque, 1);
        vTaskDelay(pdMS_TO_TICKS(100));
        send_can_message(sdo_message, SDO_ID_DRIVER_2, negative_end, 1);
        vTaskDelay(pdMS_TO_TICKS(100));
        send_can_message(sdo_message, SDO_ID_DRIVER_2, positive_end, 1);
        vTaskDelay(pdMS_TO_TICKS(100));
        send_can_message(nmt_ss_message, NMT_START_STOP_ID, nmt_start, 0);
        vTaskDelay(pdMS_TO_TICKS(100));
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_2, rpdo1_1, 0);
        vTaskDelay(pdMS_TO_TICKS(50));
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_2, rpdo1_2, 0);
        vTaskDelay(pdMS_TO_TICKS(50));
        send_can_message(r_pdo1_message, R_PDO1_ID_DRIVER_2, rpdo1_3, 1);
    }
    else {
        ESP_LOGE(TAG, "Invalid motor number");
    }
}


int32_t read_encoder_position(int driver) {
    uint8_t sdo_read_request[8] = {0x40, 0x64, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00};
    uint32_t sdo_response_id = (driver == 1) ? 0x583 : 0x582; // T_SDO COB-ID for response

    twai_status_info_t status;
    twai_get_status_info(&status);
    while (status.msgs_to_tx > 0) { // Wait for pending messages
        twai_get_status_info(&status);
    }


    // Retry up to 3 times
    for (int retry = 0; retry < 2; retry++) {
        send_can_message(sdo_message, (driver == 1) ? SDO_ID_DRIVER_1 : SDO_ID_DRIVER_2, sdo_read_request, false);

        twai_message_t rx_msg;
        if (twai_receive(&rx_msg, pdMS_TO_TICKS(100)) == ESP_OK) {
            if (rx_msg.identifier == sdo_response_id && rx_msg.data[0] == 0x43) {
                int32_t position = (rx_msg.data[7] << 24) | (rx_msg.data[6] << 16) | 
                                  (rx_msg.data[5] << 8)  | rx_msg.data[4];
                return position;
            }
        }
        // vTaskDelay(pdMS_TO_TICKS(10)); // Small delay between retries
    }
    return 2.; // Error after retries
}

void init_gpio(void) {
    gpio_config_t io_conf_output = {};
    io_conf_output.intr_type = GPIO_INTR_DISABLE;
    io_conf_output.mode = GPIO_MODE_OUTPUT;
    io_conf_output.pin_bit_mask = (1ULL<<GPIO_DIR_CONTROL) | (1ULL<<GPIO_DIR_CONTROL2);
    io_conf_output.pull_down_en = GPIO_PULLDOWN_DISABLE;
    io_conf_output.pull_up_en = GPIO_PULLUP_DISABLE;
    gpio_config(&io_conf_output);

    // Configura el pin como entrada
    gpio_config_t io_conf_input = {};
    io_conf_input.intr_type = GPIO_INTR_DISABLE;
    io_conf_input.mode = GPIO_MODE_INPUT;
    io_conf_input.pin_bit_mask = (1ULL << SENSOR) | (1ULL << SENSOR_IR_B1) | (1ULL << SENSOR_IR_B2); 
    io_conf_input.pull_down_en = 0;
    io_conf_input.pull_up_en = 0; 
    gpio_config(&io_conf_input);
}

void init_pwm(void) {
    // Configuración del PWM
    ledc_timer_config_t pwm_timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = PWM_FREQUENCY,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&pwm_timer);

    // Configuración del PWM
    ledc_timer_config_t pwm_timer2 = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = LEDC_TIMER_10_BIT,
        .timer_num = LEDC_TIMER_1,
        .freq_hz = PWM_FREQUENCY2,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ledc_timer_config(&pwm_timer2);

    // Canal del PWM
    ledc_channel_config_t pwm_channel = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .intr_type = LEDC_INTR_DISABLE,
        .gpio_num = PWM_OUTPUT_PIN,
        .duty = 0, // Ciclo de trabajo inicial
        .hpoint = 0
    };
    ledc_channel_config(&pwm_channel);

    // Canal PWM 2
    ledc_channel_config_t pwm_channel_2 = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,         // Canal 1
        .timer_sel = LEDC_TIMER_1,         // Utiliza el mismo temporizador (0)
        .intr_type = LEDC_INTR_DISABLE,    // Sin interrupciones
        .gpio_num = PWM_OUTPUT_PIN2,      // Segundo pin PWM
        .duty = 0,                         // Ciclo de trabajo inicial (0%)
        .hpoint = 0
    };
    ledc_channel_config(&pwm_channel_2);
}

void print_task(void *pv) {
    while(1){
        printf("%f|%f|%f|%f|%f\n", pos1*1., pos2*1., torque1, torque2, esp_timer_get_time()*1. / 1000000);
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

void torque_task(void *pv) {

    const float amplitude1 = 13.0;
    const float amplitude2 = 13.0;
    const float period_ms_1 = 7000;
    const float period_ms_2 = 7000;
    float time = 0.0;
    const TickType_t delay_ms = 100;

    while (1) {
        torque1 = amplitude1 * sin(2 * M_PI * time / period_ms_1);
        torque2 = amplitude2 * sin(2 * M_PI * time / period_ms_2);
        
        // set_motor_torque(1, torque1);
        set_motor_torque(2, torque2);

        time += delay_ms;
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
}

void encoder_task(void *pv) {
    while (1) {
        curr_pos2 = read_encoder_position(2);
        curr_pos1 = read_encoder_position(1);
        if (curr_pos1 == 2. || curr_pos2 == 2.){
            continue;
        }
        delta1 = curr_pos1 - prev_pose1;
        delta2 = curr_pos2 - prev_pose2;

        if (delta1 > 3600/2){
            delta1 -= 3600;
        }else if(delta1 < -3600/2){
            delta1 += 3600;
        }
        if (delta2 > 3600/2){
            delta2 -= 3600;
        }else if(delta2 < -3600/2){
            delta2 += 3600;
        }
        pos1 += delta1;
        pos2 += delta2;
        prev_pose1 = curr_pos1;
        prev_pose2 = curr_pos2;
        vTaskDelay(2);
    }
}

void app_main() {
    vTaskDelay(pdMS_TO_TICKS(3000));
    init_gpio();
    init_pwm();
    
    // Initialize CAN
    ESP_ERROR_CHECK(twai_driver_install(&g_config, &t_config, &f_config));
    ESP_ERROR_CHECK(twai_start());
    
    // Initialize motors
    init_torque_mode(1);
    vTaskDelay(pdMS_TO_TICKS(100));
    init_torque_mode(2);
    
    // Send initial heartbeat
    twai_transmit(&heartbeat_msg, portMAX_DELAY);
    
    // Clear any pending CAN messages
    twai_status_info_t status_info;
    do {
        twai_get_status_info(&status_info);
        vTaskDelay(pdMS_TO_TICKS(100));
    } while (status_info.msgs_to_tx > 0);
    
    ESP_LOGI(TAG, "System ready");
    
    set_motor_torque(1, 0.);
    set_motor_torque(2, 0.);
    
    // Create tasks (ONCE, not in a loop)
    xTaskCreatePinnedToCore(torque_task, "torque", 4096, NULL, 3, NULL,1);  // Higher priority
    xTaskCreatePinnedToCore(encoder_task, "encoder", 4096*4, NULL, 2, NULL,1);
    xTaskCreatePinnedToCore(print_task, "print", 4096, NULL, 1, NULL,0);
    
    // Let the tasks run - no while(1) needed here
    vTaskDelay(portMAX_DELAY);
}