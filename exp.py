import datetime
from bleu import computeMaps, bleuFromMaps
from tqdm import tqdm
from transformers import RobertaTokenizer, T5ForConditionalGeneration

if __name__ == '__main__':
    model_name = 'codet5-base-multi-sum'

    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/' + model_name)
    model = T5ForConditionalGeneration.from_pretrained('Salesforce/' + model_name)

    code1 = """public class ListenerContainerIdleEvent extends KafkaEvent {
        // Retrieve the consumer.
        org.apache.kafka.clients.consumer.Consumer<?,?> getConsumer();
        // How long the container has been idle.
        long getIdleTime();
        // The id of the listener (if @KafkaListener) or the container bean name.
        String getListenerId();
        // The TopicPartitions the container is listening to.
        Collection<org.apache.kafka.common.TopicPartition> getTopicPartitions();
        // Return true if the consumer was paused at the time the idle event was published.
        boolean isPaused();
        String toString();
    }"""
    code2 = """public class AnnotationJmxAttributeSource extends Object implements JmxAttributeSource, org.springframework.beans.factory.BeanFactoryAware {
        // Implementations should return an instance of ManagedAttribute if the supplied Method has the corresponding metadata.
        ManagedAttribute getManagedAttribute(Method method);
        // Implementations should return an instance of ManagedMetric if the supplied Method has the corresponding metadata.
        ManagedMetric getManagedMetric(Method method);
        // Implementations should return an array of ManagedNotifications if the supplied Class has the corresponding metadata.
        ManagedNotification[] getManagedNotifications(Class<?> clazz);
        // Implementations should return an instance of ManagedOperation if the supplied Method has the corresponding metadata.
        ManagedOperation getManagedOperation(Method method);
        // Implementations should return an array of ManagedOperationParameter if the supplied Method has the corresponding metadata.
        ManagedOperationParameter[] getManagedOperationParameters(Method method);
        // Implementations should return an instance of ManagedResource if the supplied Class has the appropriate metadata.
        ManagedResource getManagedResource(Class<?> beanClass);
        void setBeanFactory(org.springframework.beans.factory.BeanFactory beanFactory);
    }"""

    codes = [code1, code2]

    predictions = []
    idx = 0

    for code in tqdm(codes):
        input_ids = tokenizer(code, return_tensors="pt").input_ids
        generated_ids = model.generate(input_ids, max_length=30)
        res = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        predictions.append(str(idx) + '\t' + res)
        idx += 1

    (goldMap, predictionMap) = computeMaps(predictions, "./test.gold")
    this_bleu = round(bleuFromMaps(goldMap, predictionMap)[0], 2)

    print(this_bleu)


    # log_filename = '{}_{}_{}.txt'.format(class_name, model_name, datetime.datetime.now().strftime("%m%d_%H%M"))
    # with open('./log/' + log_filename, mode="w", encoding='utf-8') as f:
    #     f.write('result: {}\n'.format(res))
    #     f.write('ground truth: {}\n'.format(class_des))

