import bench_model


def main():
    for executor in [
        # '--exec trt',
        # '--exec trt --trt_fp16',
        # '--exec hidet --precision f32 --reduce_precision f32 --mma simt',
        # '--exec hidet --precision f32 --reduce_precision f32 --mma simt --parallel_k disabled',
        # '--exec hidet --precision f32 --reduce_precision f32 --mma simt --parallel_k 2',
        # '--exec hidet --precision f32 --reduce_precision f32 --mma simt --parallel_k 4',
        # '--exec hidet --precision f32 --reduce_precision f32 --mma simt --parallel_k 8',
        # '--exec hidet --precision f16 --reduce_precision f16 --mma wmma',
        '--exec ort --ort_provider cuda',
        # '--exec ort --ort_provider trt'
        # '--exec tvm',
        # '--exec ansor --tvm_trial 800',
        # '--exec autotvm --tvm_trial 1000',
    ]:
        for bs in [
            '--bs 1',
            # '--bs 16'
        ]:
            for idx in range(23):
                model = '--model resnet50_conv_{}'.format(idx)
                bench_model.main('{} {} {}'.format(executor, bs, model))


if __name__ == '__main__':
    main()