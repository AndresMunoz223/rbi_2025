#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <math.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "esp_system.h"

#include "math.h"
#include "driver/uart.h"
#include "driver/twai.h"

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

#define UART_PORT_NUM      UART_NUM_0
#define UART_BAUD_RATE     115200
#define UART_BUF_SIZE      1024


#define Convertion_1_angle_mot 1.


void uart_init() {
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };
    uart_driver_install(UART_PORT_NUM, UART_BUF_SIZE * 2, 0, 0, NULL, 0);
    uart_param_config(UART_PORT_NUM, &uart_config);
    uart_set_pin(UART_PORT_NUM, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
}


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

union IntToBytes m1_ang;
union IntToBytes m2_ang;
int conv_rel_paces_angle1 = 3600; // paces/1 grade
int conv_rel_paces_angle2 = 4480; // paces/1 grade
float conv_rel_paces_angle3 = 1.42;
int conv_rel_paces_cm = 793; // paces/1 cm
float pos_m4 = 25.4; //cm
float pos_m1 = 0; //grados
float pos_m2 = 0; //grados
float pos_m3 = 0; //grados

float motor_1_angle_applied = 0.0f;
float motor_2_angle_applied = 0.0f;
float motor_3_angle_applied = 0.0f;

static const twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(TX_GPIO_NUM, RX_GPIO_NUM, TWAI_MODE_NORMAL);
static const twai_timing_config_t t_config = TWAI_TIMING_CONFIG_50KBITS();
static const twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

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

    // vTaskDelay(pdMS_TO_TICKS(10));

    // twai_clear_receive_queue();
    // twai_clear_transmit_queue();

}

void move_motor_can(int driver, union IntToBytes angle)
{
	uint8_t start_move[6] = {0x5F,0x00,angle.bytes[0],angle.bytes[1],angle.bytes[2],angle.bytes[3]};
	uint8_t new_setpoint[6] = {0x4F,0x00,angle.bytes[0],angle.bytes[1],angle.bytes[2],angle.bytes[3]};
	if (driver == 1){

		send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_1, new_setpoint, 1);
		send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_1, start_move, 1);
	}
	else if (driver == 2)
	{
		send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_2, new_setpoint, 1);
		send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_2, start_move, 1);
	}
	else
	{
		ESP_LOGI(TAG, "Incorrect driver, must use 1 or 2");
	}
}

void set_pwm_duty_cycle(int duty) {
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

void control_pwm_cycles2(int paces) {
    if (paces < 0) {
        gpio_set_level(GPIO_DIR_CONTROL2, 0);
        paces = paces*-1;
    }
    else {
        gpio_set_level(GPIO_DIR_CONTROL2, 1);
    }
    
    set_pwm_duty_cycle2(PWM_DUTY_CYCLE * 1023 / 100);  // Establecer ciclo de trabajo
    vTaskDelay(pdMS_TO_TICKS(1000*paces/PWM_FREQUENCY2));

    set_pwm_duty_cycle2(0);  
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

void uart_thread_(void *args){

    printf("Init_UART");

    static char rx_line_buffer[UART_BUF_SIZE];
    static int line_buffer_index = 0;

    uint8_t *data = (uint8_t *)malloc(UART_BUF_SIZE);
    char *token;
    char *rest;
    char *endptr;

    float motor_1_angle = 0.0f;
    float motor_2_angle = 0.0f;
    float motor_3_angle = 0.0f;

    while(1){

        // printf("UartStuff");

        // Read data from the UART buffer
        int rx_bytes = uart_read_bytes(UART_PORT_NUM, data, UART_BUF_SIZE, 10 / portTICK_PERIOD_MS);
        
        if (rx_bytes > 0) {

            for (int i = 0; i < rx_bytes; i++) {
                char ch = data[i];


                rx_line_buffer[line_buffer_index++] = ch;


                if (ch == '\n' || line_buffer_index >= UART_BUF_SIZE - 1) {
                    rx_line_buffer[line_buffer_index - 1] = '\0'; // Null-terminate the string

                    rest = rx_line_buffer;

                    token = strtok_r(rest, "|", &rest);
                    if (token != NULL) {
                        motor_1_angle = strtof(token, &endptr);
                        
                        if (-62.0 <= motor_1_angle && motor_1_angle <= 62.0){
                                motor_1_angle_applied = motor_1_angle;
                        }
                        if (*endptr != '\0') {
                            printf("Error getting motor 1 angle: %s\n", token);
                        }
                    }


                    token = strtok_r(rest, "|", &rest);
                    if (token != NULL) {
                        motor_2_angle = strtof(token, &endptr);

                        if (-100.0 <= motor_2_angle && motor_2_angle <= 100.0){
                               motor_2_angle_applied = motor_2_angle;
                        }

                        if (*endptr != '\0') {
                            printf("Error getting motor 2 angle: %s\n", token);
                        }
                    }

                    // token = strtok_r(rest, "\n", &rest);
                    if (token != NULL) {

                        motor_3_angle = strtof(token, &endptr);
                        if (0.0 <= motor_3_angle && motor_3_angle <= 360.0){
                                motor_3_angle_applied = motor_3_angle;
                        }

                        if (*endptr != '\0') {
                            printf("Conversion error for pressure: %s\n", token);
                        }
                    }

                    line_buffer_index = 0;
                }
            }
        }

        vTaskDelay(pdMS_TO_TICKS(100));

    }

}

void scara_actuation_taks_(void *args){


    send_can_message(sdo_message, SDO_ID_DRIVER_2, activate_rpdo2_d2, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, set_accel, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, set_decel, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, target_vel, 1);
    send_can_message(nmt_ss_message, NMT_START_STOP_ID, nmt_start, 0);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_2, rpdo2_1, 0);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, negative_end, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, positive_end, 1);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_2, rpdo2_2, 0);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_2, rpdo2_3, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_2, start_op_mode_pos, 1);

    send_can_message(sdo_message, SDO_ID_DRIVER_1, activate_rpdo2_d1, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, set_accel, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, set_decel, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, target_vel, 1);
    send_can_message(nmt_ss_message, NMT_START_STOP_ID, nmt_start, 0);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_1, rpdo2_1, 0);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, negative_end, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, positive_end, 1);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_1, rpdo2_2, 0);
    send_can_message(r_pdo2_message, R_PDO2_ID_DRIVER_1, rpdo2_3, 1);
    send_can_message(sdo_message, SDO_ID_DRIVER_1, start_op_mode_pos, 1);


    while(1){

	// Driver 2
    if (-100.0 <= motor_2_angle_applied && motor_2_angle_applied <= 100.0){
        m2_ang.num = (int)round(conv_rel_paces_angle2*(motor_2_angle_applied - pos_m2));//conv_rel_paces_angle2*
        pos_m2 = motor_2_angle_applied;
	    move_motor_can(2, m2_ang);
    }        

    if (-62.0 <= motor_1_angle_applied && motor_1_angle_applied <= 62.0){
        m1_ang.num = (int)round(Convertion_1_angle_mot*conv_rel_paces_angle1*(motor_1_angle_applied - pos_m1));//conv_rel_paces_angle1*
        pos_m1 = motor_1_angle_applied;
	    move_motor_can(1, m1_ang);
    }

    if (0.0 <= motor_3_angle_applied && motor_3_angle_applied <= 360.0){
        int paces_m3 = (int)round(conv_rel_paces_angle3*(motor_3_angle_applied - pos_m3));
        pos_m3 = motor_3_angle_applied;
        control_pwm_cycles2(paces_m3);
    }

    vTaskDelay(pdMS_TO_TICKS(30));

    }
    ESP_ERROR_CHECK(twai_stop());
	
}

void app_main(void)
{

	for (int i = 3; i > 0; i--) {
        printf("Program starting in %d\n", i);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    init_gpio();
    init_pwm();
    set_pwm_duty_cycle(0); 

    set_pwm_duty_cycle(PWM_DUTY_CYCLE * 1023 / 100);  // Establecer ciclo de trabajo

    ESP_ERROR_CHECK(twai_driver_install(&g_config, &t_config, &f_config));
    ESP_LOGI(TAG, "Driver installed");
    ESP_ERROR_CHECK(twai_start());
    ESP_LOGI(TAG, "Driver started");

    uart_init();

    printf(" I did it");
    ESP_LOGI(TAG, "I did it");   

    xTaskCreatePinnedToCore(scara_actuation_taks_,"scara_task",4098,NULL,1, NULL, 0);
    xTaskCreatePinnedToCore(uart_thread_,"uart_task",4098,NULL,1, NULL, 0);
    

}



